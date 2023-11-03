import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--address",
        action="store",
        default='localtest.me',
        type=str,
        help="ICL infrastructure address, default: localtest.me",
    )


@pytest.fixture(scope="session")
def address(pytestconfig):
    yield pytestconfig.getoption("--address")
