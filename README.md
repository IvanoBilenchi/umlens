## UMLens - a Python framework for the automated analysis of UML documents

### Author

[Ivano Bilenchi](https://ivanobilenchi.com)

### Description

**UMLens** is a Python framework for the automated analysis of UML documents. The system is able to analyze UML class diagrams in order to detect design patterns and dependency cycles between class instances, and to compute useful metrics, including ones that can be used to estimate the degree of technical debt of a certain software system.

The system has been developed as the end of year project for the *Advanced Software Engineering* and *Secure Programming Laboratory* exams at the [*Polytechnic University of Bari*](http://www.poliba.it).


### Prerequisites

UMLens has been tested on **macOS 10.15 Catalina**, though it should work on earlier macOS releases and other OSes as well. It just requires a working [Python 3](https://python.org) interpreter.


### Installation

`git clone https://github.com/IvanoBilenchi/umlens.git`

To uninstall UMLens, just delete the `umlens` dir.

### Usage

UMLens can be run by launching the `umlens.py` script via terminal, which accepts a number of subcommands and flags.

To list the available subcommands, run `python3 umlens.py -h`. If you need help with a specific subcommand, run `python3 umlens.py <subcommand> -h`.

Input files are UML class diagrams exported via [Visual Paradigm CE](https://www.visual-paradigm.com) in XML format (simplified). For metrics computation, a JSON configuration file must be provided as well via the `-c` flag, in order to specify weights that should be given to specific metrics while computing the *technical debt ratio*. Keys for metrics are just their class names converted to snake_case. Here's a sample configuration:

```json
{
  "classes_in_pattern": 100.0,
  "avg_inheritance_depth": 100.0,
  "classes_in_pattern_ratio": 100.0,
  "avg_methods_per_class": 100.0,
  "avg_relationships_per_class": 100.0,
  "classes_in_cycle_ratio": 100.0,
  "development_cost": 10000.0
}
```

### License

UMLens is available under the MIT license. See the [LICENSE](./LICENSE) file for more info.
