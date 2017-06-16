import os
import time
import re
import tempfile
import subprocess
try:
	import configparser as ConfigParser
except:
	import ConfigParser
from collections import defaultdict as DD

__version__ = '0.0.8'
configfile = os.path.expanduser('~/.avryprc')

try:
	import colorama as COLOR
except:
	COLOR = type('fake_colorama',(),{'__getattr__':(lambda s,x:type('fake_colorama.'+x,(),{'__getattr__':(lambda ss,y:'')})())})()

def oss(cmd, *a, **kw):
	fcmd = cmd.format(*a, **kw)
	print(COLOR.Fore.RED + fcmd + COLOR.Style.RESET_ALL)
	return subprocess.Popen(fcmd, stdout=subprocess.PIPE, shell=True).stdout.read()

def write_file_in_tempdir(nf, content):
	tmpincdir = tempfile.mkdtemp(prefix='avryp_tempdir_')
	with open(tmpincdir + '/' + nf, 'w') as f:
		f.write(content)
	return tmpincdir

def fixgpio(gpio):
	oss('echo "%d" > /sys/class/gpio/unexport' % int(gpio))
	time.sleep(0.1)  #https://raspberrypi.stackexchange.com/questions/23162/gpio-value-file-appears-with-wrong-permissions-momentarily

def config_get_or_none(cfg, section, option, default=None):
	try:
		return cfg.get(section, option)
	except:
		return default

class Fuses(object):
	def __init__(self, chip, cplt=None):
		self.chip = chip
		self.cplt = cplt or Avryp()
	def fromavrdude(self):
		c = self.cplt.avrdude(' -p {}', self.chip)
		d = c.split('Fuses OK ')[1].split('\n')[0]
		rfa = re.findall('([a-zA-Z]+):([a-fA-F0-9]+)', c)
		self.fuses = dict(map(lambda x:(x[0], int(x[1], 16)), rfa))
		return self
	def getmonobit(self, fuse, bitno):
		return ( self.fuses[fuse] & (1<<bitno) ) >> bitno
	def getbits(self, fuse, lowestbit, bitsize, littleendian = False):
		rb = ''
		for bit in range(lowestbit + bitsize - 1, lowestbit - 1, -1):
			rb = str(self.getmonobit(fuse, bit))
		if littleendian:
			rb = rb[::-1]
		r = int(rb, 2)
		return r

class Chip(object):
	def __init__(self, name, cplt):
		self.name = name
		self.cplt = cplt

	def f_cpu_avrdude(self):
		if 'attiny13' in self.name:
			f = Fuses('attiny13', self.cplt).fromavrdude()
			cksel = f.getbits('L', 0, 2)
			if cksel == 0:
				raise Exception("Clock is external (CKSEL=00)")
			elif cksel == 1:
				return 4800000/8
			elif cksel == 2:
				return 9600000/8
			elif cksel == 3:
				return 128000/8
		raise Exception("Can't determine F_CPU from avrdude")

class SourceCode(object):
	def __init__(self, fn, content=None, cplt=None):
		self.sourcefn = fn
		self.fn = None
		self.content = content
		self.output = None
		self.cplt = cplt
		self.clone = None
		self.incdirs = []
		if 'extension' not in dir(self):
			raise Exception("ext missing")
		if 'gcc' not in dir(self):
			raise Exception("gcc missing")
		if 'flags' not in dir(self):
			raise Exception("flags missing")
	def precompile(self):
		fnonly = self.sourcefn.split('/')[-1]
		def avrvar(match):
			name = match.group(1)
			return str(self.cplt.vars[name])

		fullcontent = self.getcontent()

		if '\n#include <AVRYPFunctions>' in fullcontent:
			fullcontent = fullcontent.replace('#include <AVRYPFunctions>','')
		if '\n#include <AVRYPVariables>' in fullcontent:
			fullcontent = re.sub('\$avryp_([a-zA-Z0-9_]+)',avrvar,fullcontent)
			fullcontent = fullcontent.replace('#include <AVRYPVariables>','')

		f = tempfile.NamedTemporaryFile(prefix=fnonly+'___', suffix=self.extension, delete=False)
		f.write(fullcontent)
		f.close()
		return f.name
	def getcontent(self):
		if self.content == None:
			self.content = open(self.sourcefn, 'r').read()
		return self.content
	def compile(self, output=None):
		cplt = self.cplt
		incs = ['.'] + cplt.incdirs + self.incdirs

		if self.extension in '.c .cpp'.split():
			AVRYP_H = '''
#define SETOUTPUT(ddr, n) ddr |= _BV(n);
#define SETINPUT(ddr, n) ddr &= ~_BV(n);
#define SETHIGH(port, n) port |= _BV(n);
#define SETLOW(port, n) port &= ~_BV(n);
#define GETLEVEL(port, n) ((port & _BV(n)) > 0)
#define TOGGLE(port, n) if(GETLEVEL(port,n)){SETLOW(port,n)}else{SETHIGH(port,n)}
'''
			tmpincdir = write_file_in_tempdir('__avryp.h', AVRYP_H)
			incs.append(tmpincdir)

		precomp = self.precompile()
		objfile = output or precomp + '.o'

		cmd = self.gcc + ' ' + self.flags + ' ' + precomp + ' -mmcu={chip} -DF_CPU={freq} {defines} -o' + objfile + ' -c '
		cmd += ''.join( map(lambda x:" -I"+x, incs) )
		cplt.s(cmd)
		return objfile
	def add_include_dir(self, d):
		self.incdirs.append(d)
	def add_header(self, nf, content):
		tmpincdir = write_file_in_tempdir(nf, content)
		self.add_include_dir(tmpincdir)

def createSourceCodeType(vext, vgcc, vflags):
	name = vext.upper()
	class SourceCodeType(SourceCode):
		gcc = vgcc
		flags = vflags
		extension = '.'+vext
		__name__ = 'SourceCode_'+name
	return SourceCodeType

SourceCodeTypes = {
	'C':   createSourceCodeType('c','avr-gcc','-Wall -Os -std=c99'),
	'CPP': createSourceCodeType('cpp','avr-g++','-Wall -Os'),
	'ASM': createSourceCodeType('S','avr-g++','-Wall -Os -x assembler-with-cpp'),
}

class Avryp(object):
	def __init__(self, dryrun=False):
		self.config = ConfigParser.ConfigParser()
		self.config.read([os.path.expanduser('~/.avryprc')])

		self.sources = []
		self.defines = []
		self.vars = {}
		self.avrvars = {}
		self.objs = []
		self.setavr('defines', '')
		self.dryrun = dryrun
		self.incdirs = []

		self.haa =             config_get_or_none(self.config, 'arduino', 'haa') #/path/to/hardware/arduino/avr/
		self.avrdudebin =      config_get_or_none(self.config, 'binaries', 'avrdude', 'avrdude')
		self.avrdudeprogtype = config_get_or_none(self.config, 'binaries', 'avrdude_progtype', 'linuxgpio')
		self.avrobjcopybin =   config_get_or_none(self.config, 'binaries', 'avrobjcopy', 'avr-objcopy')
		self.avrsizebin =      config_get_or_none(self.config, 'binaries', 'avrsize', 'avr-size')
		self.avrgccbin =       config_get_or_none(self.config, 'binaries', 'avrgcc', 'avr-gcc')
		self.avrgppbin =       config_get_or_none(self.config, 'binaries', 'avrgpp', 'avr-g++')
		self.load_chips()

	def formatstring(self, cmd, *a, **kw):
		kw.update(self.getallavrs())
		return cmd.format(*a, **kw)
	def cmdself(self, cmd):
		return self.s(cmd)
	def s(self, cmd, *a, **kw):
		cmd = self.formatstring(cmd, *a, **kw)
		if self.dryrun:
			print(COLOR.Fore.RED + cmd + COLOR.Style.RESET_ALL)
			return ''
		else:
			return self._s(cmd)
	def _s(self, cmd, *a, **kw):
		return oss(cmd, *a, **kw)

	def avrgcc(self, params, *a, **kw):
		cmd = '{} {} 2>&1'.format(self.avrgccbin, params)
		c = self.s(cmd, *a, **kw)
		return c
	def avrobjcopy(self, params, *a, **kw):
		cmd = '{} {} 2>&1'.format(self.avrobjcopybin, params)
		c = self.s(cmd, *a, **kw)
		return c
	def avrsize(self, params, *a, **kw):
		cmd = '{} {} 2>&1'.format(self.avrsizebin, params)
		c = self.s(cmd, *a, **kw)
		return c
	def avrdude(self, params, *a, **kw):
		cmd = '{} -c {} {} 2>&1'.format(self.avrdudebin, self.avrdudeprogtype, params)
		c = self.s(cmd, *a, **kw)
		gpio = re.findall("Can't export GPIO (.*), already exported/busy.: Device or resource busy", c)
		if gpio:
			fixgpio(gpio[0])
			c = self.s(cmd, *a, **kw)
		if re.findall("Can't open gpioX/direction: Permission denied",c):    #avrdude bug: gpio port is still exported
			c = self.s(self.avrdudebin+' -c '+self.avrdudeprogtype+' -p AT90PWM2 -F 2>&1')
			fixgpio(re.findall("Can't export GPIO (.*), already exported/busy.: Device or resource busy", c)[0])
			raise Exception("Requires root permissions (GPIO)")
		return c

	def load_chips(self):
		c = open('/etc/avrdude.conf','r').read()
		lastidx = 0
		CHIPS = {}
		for m in re.compile('signature[ =\t]*0x([^ ;]*) *0x([^ ;]*) *0x([^ ;]*) *;').finditer(c):
			st, g = m.start(), m.group(0)
			partidx = c.rfind('part',lastidx,st)
			chip = re.findall('desc[ =\t]*(.*);', c[partidx:st])[0][1:-1]
			sig = ''.join(m.groups())
			CHIPS[chip] = int(sig, 16)
		self.chips = CHIPS
	def identify_chip_sig(self, unkchip):
		if unkchip == 0:
			raise Exception("Avrdude can't identify the chip (signature = 0x000000).")
		if not unkchip in self.chips.values():
			raise Exception("Unknown chip signature: 0x%06x"%unkchip)
		return self.chips.keys()[self.chips.values().index(unkchip)] #todo
	def identify_connected_chips(self, verbose=False): #todo: not reliable
		r = []
		try:
			r.append(self.identify_connected_chip(verbose))
		except:
			pass
		return r
	def identify_connected_chip(self, verbose=False):
		c = self.avrdude(' -p AT90PWM2 -F')
		if verbose:
			print(c)
		if not 'Expected signature' in c:
			return randchip
		sig = int(re.findall('Device signature = (.*)', c)[0], 16)
		return self.identify_chip_sig(sig)

	def setvar(self, n, v):
		self.vars[n] = v
	def add_define(self, v):
		self.defines.append(v)
		self.setavr('defines', ' '.join(map(lambda x:'-D'+x, self.defines)))
	def add_include_dir(self, d):
		self.incdirs.append(d)
	def add_header(self, nf, content):
		tmpincdir = write_file_in_tempdir(nf, content)
		self.add_include_dir(tmpincdir)
	def add_CXAPV(self):
		self.add_source('cxapv.cpp', 'extern "C" void __cxa_pure_virtual(){while(1);}')
	def add_source(self, fn, content=None, astype=None, fromarduino=None):
		if fromarduino:
			if not self.haa:
				raise Exception("HAA unknown: set config/arduino/haa in '%s' to the Arduino/hardware/arduino/avr path"%configfile)
			return self.add_source(os.path.join(self.haa, fn))

		if not os.path.exists(fn) and not content:
			raise Exception("File doesn't exist: {}".format(fn))
		clsok = filter(lambda x:fn.endswith(x.extension), SourceCode.__subclasses__())
		if len(clsok)==0:
			raise Exception("Can't find the type of '{}', please check the extension (currently accepted: {})".format(fn, map(lambda x:x.extension, SourceCode.__subclasses__())))
		assert len(clsok)==1, "Error (add_source): number of corresponding classes:"+str(len(clsok))
		cls = clsok[0]
		s = cls(fn, content)
		s.cplt = self
		self.sources.append(s)
		return s

	def getallavrs(self):
		return self.avrvars
	def avrexists(self, a):
		return a in self.avrvars
	def getavr(self, a):
		return self.avrvars[a]
	def setavr(self, a, v):
		self.avrvars[a] = v
		if a == 'chip':
			self.chip = Chip(v, self)
		return self
	def freq(self, v):
		self.setavr('freq', v)
	def chip(self, v):
		if v.__class__ == int: #todo: not reliable
			cchips = self.identify_connected_chips(False)
			if v < len(cchips):
				v = cchips[v]
		self.setavr('chip', v.lower())

	def _prebuild(self):
		if not self.avrexists('chip'):
			raise Exception("No chip given")
		if not self.avrexists('freq'):
			self.setavr('freq', self.chip.f_cpu_avrdude())
			print("Frequency from avrdude: "+str(self.getavr('freq')))
		return 1

	def build(self, output=None, flush=True):
		self.setavr('output', output or 'program')
		if not self.sources:
			raise Exception("Build error: no source files")
		if not self._prebuild():
			raise Exception("Build error: prebuild")
		self.objs = []
		for sc in self.sources:
			obj = sc.compile()
			self.objs.append(obj)
		self.avrgcc(' -mmcu={chip} -o{output} '+(' '.join(self.objs)))
		if flush:
			map(lambda x:self.cmdself('rm "%s"'%x), self.objs)
		self.avrobjcopy(' -O ihex {output} {output}.hex')
		print(self.avrsize(' -C --mcu={chip} {output}'))
		if flush:
			self.cmdself('rm "{output}"')
		return self

	def flash(self, output=None, flush=False):
		assert self.avrexists('chip'), "Chip must be set before flashing"
		if output:
			hexfile = repr(output)
		elif self.avrexists('output'):
			hexfile = repr(self.getavr('output')+'.hex')
		else:
			raise Exception("A project must be built before flashing or a filename must be given as an argument to flash")
		ret = self.avrdude('-p {chip}')
		if 'AVR device initialized' not in ret and not self.dryrun:
			print("Error: uploading failed because AVR device can't be initialized")
			print(ret)
			return
		print(self.avrdude('-p {chip} -U flash:w:' + hexfile + ':i'))
		if flush:
			self.cmdself('rm '+hexfile)

	def build_flash(self, *a, **kw):
		self.build(*a, **kw)
		self.flash(*a, **kw)

