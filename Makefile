.PHONY: test verify

test:
	python3 -m unittest discover -s tests -v

verify: test
	python3 verify.py --output results/verification.json
	python3 verify_thresholds.py --output results/threshold_verification.json
