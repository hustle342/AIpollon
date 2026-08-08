# Contributing

Quick start for contributors:

- Create a virtual environment and activate it:
```
python -m venv .venv
.\.venv\Scripts\activate
```
- Install dev requirements (if any):
```
pip install -r requirements.txt
```
- Run tests:
```
python -m unittest discover -v
```

Code style: keep diffs small and focused. Add tests for new functionality. Use the existing test harness under `tests/`.
