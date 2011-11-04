if __name__ == '__main__':
	import doctest
	import atcommands
	import config
	import dummy
	doctest.testmod(atcommands)
	doctest.testmod(config)
	doctest.testmod(dummy)
