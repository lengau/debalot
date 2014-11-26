PB_DIR=protobufs
PB_PY=lib
PB_COMPILER=protoc -I=$(PB_DIR) --python_out=$(PB_PY)
PB_PY_SFX=_pb2.py
# Default target executed when no arguments are given to make.
default_target: all
.PHONY : default_target

all: python_pb2 python_packages
.PHONY : all

python_pb2: $(PB_PY)/person$(PB_PY_SFX) $(PB_PY)/debian_package$(PB_PY_SFX)
.PHONY : python_pb2

python_packages: lib/__init__.py
.PHONY : python_packages

$(PB_PY)/%$(PB_PY_SFX): $(PB_DIR)/%.proto
	$(PB_COMPILER) $<

%/__init__.py:
	touch $@

# Delete any generated pb2 files. Delete directories that only held them.
clean:
	find . -name __init__.py -empty -delete
	find . -name *_pb2.py -delete
	find . -name *.pyc -delete
	find . -type d -empty -delete
