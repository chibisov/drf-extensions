build_docs:
	PYTHONIOENCODING=utf-8 python docs/backdoc.py --title "Django Rest Framework extensions documentation" < docs/index.md > docs/index.html
	python docs/post_process_docs.py

watch_docs:
	make build_docs
	watchmedo shell-command -p "*.md" -R -c "make build_docs" docs/
