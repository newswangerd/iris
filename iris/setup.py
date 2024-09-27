from setuptools import setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="iris",
    version="1.0.0",
    package_dir={"": "."},
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/newswangerd/iris",
    description="Intelligent Real-time Interpretation System",
)
