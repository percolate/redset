# History

## 0.3

- Add builtin serializer `NamedtupleSerializer`
- Improve lock re: redis' spotty timestamp precision
- Increase test coverage
- Add coveralls to travis-CI

## 0.2.3

- Documentation updates

## 0.2.2

- Use `setuptools` now that distribute has been merged back into it

## 0.2.1

- Change serializer interface to match `json` (dump, load `->` dumps, loads)

## 0.2.0

- Spiked documentation with sphinx.
- Converted docstrings to ReST.

## 0.1.2

- Removed used of `mockredispy` because of its inconsistency with how redis
  actually behaves.

