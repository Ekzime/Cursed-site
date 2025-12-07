#!/bin/bash
# Run router integration tests

cd /home/ekz/Documents/Projects/cursed-board/backend
python -m pytest tests/integration/test_routers.py -v --tb=short
