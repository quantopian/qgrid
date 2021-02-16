# Module version
version_info = (2, 0 , 0, 'alpha', 0)

# Module version stage suffix map
_specifier_ = {'alpha': 'a', 'beta': 'b', 'candidate': 'rc', 'final': ''}

# Module version accessible using qgrid.__version__
__version__ = '%s.%s.%s%s'%(version_info[0], version_info[1], version_info[2],
  '' if version_info[3]=='final' else _specifier_[version_info[3]]+str(version_info[4]))
