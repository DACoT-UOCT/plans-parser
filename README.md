# UTC Plans Parser module of the DACoT project 

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=DACoT-UOCT_plans-parser&metric=alert_status)](https://sonarcloud.io/dashboard?id=DACoT-UOCT_plans-parser) [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=DACoT-UOCT_plans-parser&metric=coverage)](https://sonarcloud.io/dashboard?id=DACoT-UOCT_plans-parser) [![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=DACoT-UOCT_plans-parser&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=DACoT-UOCT_plans-parser) [![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=DACoT-UOCT_plans-parser&metric=security_rating)](https://sonarcloud.io/dashboard?id=DACoT-UOCT_plans-parser)

## Run Tests  

To run all tests in the project, run this command from the root directory of the repository:

```bash
python -m unittest -v
```
For security reasons, the test that connects to the UTC system in the UOCT network is ignored in CI. To run it, you have to follow this steps:

```bash
export DACOT_UOCT_CTRL_HOST='UTC system address'
export DACOT_UOCT_CTRL_USER='UTC system username'
export DACOT_UOCT_CTRL_PASS='UTC system user password'
python -m unittest -v tests.test_telnet_uoct.TestTelnetExecutorUOCT
```
