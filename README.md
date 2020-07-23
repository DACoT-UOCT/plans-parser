# UTC Schedules builder module of DACoT

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=DACoT-UOCT_plans-parser&metric=alert_status)](https://sonarcloud.io/dashboard?id=DACoT-UOCT_plans-parser) [![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=DACoT-UOCT_plans-parser&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=DACoT-UOCT_plans-parser) [![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=DACoT-UOCT_plans-parser&metric=security_rating)](https://sonarcloud.io/dashboard?id=DACoT-UOCT_plans-parser) [![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=DACoT-UOCT_plans-parser&metric=reliability_rating)](https://sonarcloud.io/dashboard?id=DACoT-UOCT_plans-parser) [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=DACoT-UOCT_plans-parser&metric=coverage)](https://sonarcloud.io/dashboard?id=DACoT-UOCT_plans-parser) [![Bugs](https://sonarcloud.io/api/project_badges/measure?project=DACoT-UOCT_plans-parser&metric=bugs)](https://sonarcloud.io/dashboard?id=DACoT-UOCT_plans-parser) [![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=DACoT-UOCT_plans-parser&metric=code_smells)](https://sonarcloud.io/dashboard?id=DACoT-UOCT_plans-parser) [![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=DACoT-UOCT_plans-parser&metric=vulnerabilities)](https://sonarcloud.io/dashboard?id=DACoT-UOCT_plans-parser)

## Build

Execute this command in the root folder of the project:

```bash
docker build -t backend:`tag` .
```

## Deploy

To deploy the stack run the following command:

```bash
bash deploy.sh
```

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
