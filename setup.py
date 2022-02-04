import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="urn-randomization",
    version="0.0.1",
    author="Research Computing Group",
    description="Urn randomization for group assignment in randomized experiments",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    packages=setuptools.find_packages(include=["urand"]),
    include_package_data=True,
    license_file="LICENSE",
    install_requires=[
        "confuse",
        "SQLAlchemy",
        "click",
        "Flask",
        "pandas",
        "numpy",
        "bokeh",
        "wtforms_alchemy",
        "flask_wtf",
        "sqlalchemy-datatables ",
        "flask_bootstrap",
        "scipy",
        "datatables",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    package_data={"urand": ["config_default.yaml"]},
    entry_points="""
        [console_scripts]
        urn=urand.cli:cli
    """,
)
