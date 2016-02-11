require 'github/markup'

output = File.open('readme.html','w')

path = File.join(File.dirname(__FILE__), '../README.rst')
output << GitHub::Markup.render(path, File.read(path))
output.close