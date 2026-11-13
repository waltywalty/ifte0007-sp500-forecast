# Invented 21-close feature example

From the repository root, run:

```sh
python3 evidence/synthetic/feature_example/check_feature.py
```

The standard-library check constructs 20 daily log returns from 21 invented closes, annualises their mean squared return and subtracts the result from invented implied variance. It returns an annualised realised variance of approximately 0.03184949 and a gap of approximately 0.00815051. This fixture demonstrates arithmetic on invented observations.
