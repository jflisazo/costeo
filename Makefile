.PHONY: typecheck typecheck-py typecheck-ts

typecheck: typecheck-py typecheck-ts

typecheck-py:
	pyright

typecheck-ts:
	cd frontend && npm run typecheck
