build_docs:
	python docs/backdoc.py --source docs/index.md --title "Django Rest Framework extensions documentation" > docs/index.html
	python docs/post_process_docs.py

watch_docs:
	make build_docs
	watchmedo shell-command -p "*.md" -R -c "make build_docs" docs/