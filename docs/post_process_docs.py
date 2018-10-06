docs_file_path = 'docs/index.html'
docs_file_content = open(docs_file_path, 'r', encoding='utf8').read()[:-len('</html>')]
docs_file = open(docs_file_path, 'w', encoding='utf-8')
metrika_file_content = open('docs/metrika_code.txt', 'r', encoding='utf-8').read()
docs_file.write(docs_file_content + metrika_file_content + '</html>')
