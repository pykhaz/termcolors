
__version__ = "0.9.3"

# "0.9.3"  # 26-01-05 -- name change → termcolours
# "0.9.2"  # 26-01-03 -- refactored for integration tests:
#                      - pytest MUST expect SystemExit; otherwise
#                        the test will fail. Now `quit()` returns `__QUIT__`,
#                        which is passed in `num_to_ansi()` to `main()`,
#                        which returns 0 → test passes
# "0.9.1"  # 26-01-01 -- printing colours in batch-file mode debugged,
#                     -- added vertical lines for palette
#                     -- APPNAME and ROOTPATH moved do __init__.py
# "0.9.0"  # 25-12-31 -- palette
# "0.8.5"
