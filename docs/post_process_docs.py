docs_file_path = 'docs/index.html'
docs_file_content = open(docs_file_path, 'r').read()[:-len('</html>')]
docs_file = open(docs_file_path, 'w')
metrika_file_content = open('docs/metrika_code.txt', 'r').read()
docs_file.write(docs_file_content + metrika_file_content + '</html>')