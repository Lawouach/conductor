# -*- coding: utf-8 -*-
import ConfigParser

__all__ = ['Config']

class Config(object):
    @staticmethod
    def from_ini(filepath, encoding='ISO-8859-1'):
        config = ConfigParser.ConfigParser()
        config.readfp(file(filepath, 'rb'))

        conf = Config()
        for section in config.sections():
            section_prop = Config()
            section_prop.keys = []
            setattr(conf, section, section_prop)
            for option in config.options(section):
                section_prop.keys.append(option)
                value = Config._convert_type(config.get(section, option).decode(encoding))
                setattr(section_prop, option, value)

        return conf

    @staticmethod
    def _convert_type(value):
        """Do dummy conversion of the string 'True', 'False' and 'None'
        into their object equivalent"""
        if value == 'True':
            return True
        elif value == 'False':
            return False
        elif value == 'None':
            return None
        try:
            return int(value)
        except:
            pass
        return value

    def get(self, section, option, default=None, raise_error=False):
        if hasattr(self, section):
            obj = getattr(self, section, None)
            if obj and hasattr(obj, option):
                return getattr(obj, option, default)

        if raise_error:
            raise AttributeError("%s %s" % (section, option))

        return default

    def get_section_by_suffix(self, prefix, suffix, default=None):
        key = "%s%s" % (prefix, suffix)
        return getattr(self, key, default)


    def has_options(self, section, options):
        if not hasattr(self, section):
            return False

        if isinstance(options, str):
            options = [options]

        obj = getattr(self, section, None)
        for option in options:
            if not (obj and hasattr(obj, option)):
                return False

        return True
