.PHONY: install test lint clean

install:
	pip install -r requirements.txt
	pip install -e .

test:
	python -m pytest src/video_frame_capture/tests/ -v

lint:
	flake8 src/ --max-line-length=100 --extend-ignore=E203,W503

clean:
	rm -rf build/ dist/ *.spec
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
