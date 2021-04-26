# Modifications copyright (C) 2021 8080 Labs GmbH

# - set version_info = (0, 0, 1, "final")

version_info = (0, 0, 2, "alpha")

_specifier_ = {"alpha": "a", "beta": "b", "candidate": "rc", "final": ""}

__version__ = "%s.%s.%s%s" % (
    version_info[0],
    version_info[1],
    version_info[2],
    _specifier_[version_info[3]],
)
