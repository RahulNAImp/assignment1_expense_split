# Harness feedback for coding agent — run-001

Repair the implementation in `src/` so that the failing gates pass.
Rules (constitution IV): do NOT edit the spec, the tests, `.harness/`, or thresholds;
do NOT add skip/xfail/noqa/nosec to silence a gate. Fix the root cause.

## G1 Lint & format — FAIL

Summary: 3 lint violation(s), 0 file(s) need formatting

- `I001` tests/contract/test_storage.py:3 — Import block is un-sorted or un-formatted
- `I001` tests/property/test_invariants.py:4 — Import block is un-sorted or un-formatted
- `I001` tests/unit/test_money.py:3 — Import block is un-sorted or un-formatted

## G3 Spec tests — FAIL

Summary: 0/4 passed, 4 failed, 0 skipped

### Failed test `::tests.contract.test_storage`
- Acceptance criterion: n/a
- Expected vs observed: `collection failure`
```text
ImportError while importing test module '/Users/rahulnandanwar/Documents/Stuff/Bits Study material/AI Argumented SDLC/assignment 1/Assignment-1/Part-1A/tests/contract/test_storage.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../../../../../../../.local/share/uv/python/cpython-3.11.17-macos-aarch64-none/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/contract/test_storage.py:6: in <module>
    from splitkaro.cli import main
E   ModuleNotFoundError: No module named 'splitkaro'
```

### Failed test `::tests.property.test_invariants`
- Acceptance criterion: n/a
- Expected vs observed: `collection failure`
```text
ImportError while importing test module '/Users/rahulnandanwar/Documents/Stuff/Bits Study material/AI Argumented SDLC/assignment 1/Assignment-1/Part-1A/tests/property/test_invariants.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../../../../../../../.local/share/uv/python/cpython-3.11.17-macos-aarch64-none/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/property/test_invariants.py:14: in <module>
    from splitkaro.cli import main
E   ModuleNotFoundError: No module named 'splitkaro'
```

### Failed test `::tests.unit.test_money`
- Acceptance criterion: n/a
- Expected vs observed: `collection failure`
```text
ImportError while importing test module '/Users/rahulnandanwar/Documents/Stuff/Bits Study material/AI Argumented SDLC/assignment 1/Assignment-1/Part-1A/tests/unit/test_money.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../../../../../../../.local/share/uv/python/cpython-3.11.17-macos-aarch64-none/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_money.py:4: in <module>
    from splitkaro.errors import ValidationError
E   ModuleNotFoundError: No module named 'splitkaro'
```

### Failed test `::tests.unit.test_performance`
- Acceptance criterion: n/a
- Expected vs observed: `collection failure`
```text
ImportError while importing test module '/Users/rahulnandanwar/Documents/Stuff/Bits Study material/AI Argumented SDLC/assignment 1/Assignment-1/Part-1A/tests/unit/test_performance.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../../../../../../../.local/share/uv/python/cpython-3.11.17-macos-aarch64-none/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_performance.py:6: in <module>
    from splitkaro.cli import main
E   ModuleNotFoundError: No module named 'splitkaro'
```


## G4 Coverage — FAIL

Summary: None% line coverage (threshold 90%)

- Uncovered lines: {}
