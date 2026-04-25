# StatChallenges Implementation Guide

StatChallenges is a pytest-based framework for comparing statistical
toolkit implementations. It lives in the StatAnalysis repository under
`Challenges/` and is installed to `$STATCHALLENGES` (set automatically
after `asetup`).

## Writing an Implementation

No repository clone is needed — use the central release on CVMFS.

### Step 1: Setup

```bash
setupATLAS
asetup StatAnalysis,latest,main
# $STATCHALLENGES is now set to the CVMFS challenges directory
```

### Step 2: Read Suite Requirements

```bash
pytest $STATCHALLENGES/suites/test_hist.py --help
```

This prints the required function signature, parameters, and return
dictionary keys.

### Step 3: Write the Solver

Create a local Python file (e.g., `my_toolkit_impl.py`). Define the
required function with the exact signature from `--help`. The function
must return a dictionary of computed quantities.

Example skeleton for `test_hist.py`:

```python
def compute_simple_histogram_model_limit(hist_file_path):
    """
    hist_file_path: path to a ROOT file containing histograms
    with naming convention <Region>/<Sample>/<Variation>.
    <Variation>="Nominal" for nominal, <Sample>="Data" for
    observed data. Variations with only _Up or _Down should
    be symmetrized. The "Signal" sample is scaled by a
    signal strength POI, mu.

    Returns a dictionary with keys:
      "yield_b", "yield_b_err", "yield_b_err_up",
      "yield_b_err_down",
      "yield_b_alpha_WeightBasedModeling_0p5",
      "yield_s", "yield_s_err",
      "dnll_alpha_WeightBasedModeling_0p5",
      "cls_obs_limit", "cls_obs_lim_err",
      "cls_exp_lim", "cls_exp_lim_err",
      "cls_1sig_lim", "cls_1sig_lim_err"
    """
    # Implementation here
    return {...}
```

### Step 4: Test

```bash
pytest $STATCHALLENGES/suites/test_hist.py --impls my_toolkit_impl.py
```

## Comparing Multiple Implementations

Run multiple implementations together to compare results:

```bash
pytest $STATCHALLENGES/suites/test_hist.py \
    --impls my_impl.py,xRooFit.py
```

Implementation files may be:

- Local files (path to `.py`)
- Installed implementations (discovered from `STATANA_IMPL_DIR` or
  `DATAPATH` environment variables)

Comparison mode is essential for test answers that lack a reference
value — passing is based on whether the answer matches the majority.

## Available Suites

List all discovered suites:

```bash
pytest $STATCHALLENGES --ls
```

Current suites include:

- **test_2bin**: Simple two-bin model with post-fit μ calculation.
  Function: `compute_postfit_mu(bkg_yield, sig_yield_nominal,
  observed_events)` → `{"mu_hat", "mu_hat_err"}`
- **test_hist**: Multi-bin histogram model with limit calculation.
  Function: `compute_simple_histogram_model_limit(hist_file_path)` →
  yields, uncertainties, NLL values, CLs limits

## Test Result Evaluation

Results are compared using `math.isclose` with `rel_tol=1e-3` and
`abs_tol=1e-3`. The framework produces:

- **Pass**: value matches reference (or majority)
- **Fail**: value differs or key is missing
- **Observed**: no reference available, recorded for comparison

JUnit XML reports are written to `test-reports/junit-report.xml`.

## Writing a New Test Suite

Contributing a new suite requires cloning the StatAnalysis repository.

### Step 1: Clone and Override

```bash
setupATLAS
asetup StatAnalysis,latest,main
git clone https://gitlab.cern.ch/atlas/StatAnalysis.git
cd StatAnalysis
export STATCHALLENGES=$PWD/Challenges
```

### Step 2: Create the Suite

Create `Challenges/suites/test_my_challenge.py` following this pattern:

```python
import sys

def test_my_test():
    """
    Describe the challenge.

    Implement function_name(arg1, arg2) that returns a
    dictionary of answers.
    """
    arg1 = "some_input"
    arg2 = 42

    def reference_solution(arg1, arg2):
        return {"answer1": 3.14, "answer2": 2.72}

    return {
        "subject_fn": "function_name",
        "args": [arg1, arg2],
        "solution": reference_solution,
    }
```

### Key Points

- Test functions must start with `test_` and return a dictionary with
  `"subject_fn"`, `"args"`, and `"solution"` keys
- The `"solution"` is a callable that receives the same args and returns
  the reference dictionary. Set to `None` if no analytic reference
  exists (comparison mode only)
- Use Python docstrings extensively — the framework extracts them to
  generate the `--help` output

### Step 3: Test Locally

```bash
pytest $STATCHALLENGES/suites/test_my_challenge.py --impls my_impl.py
```

## Environment Variables

| Variable             | Description |
| -------------------- | ----------- |
| `STATCHALLENGES`     | Path to challenges directory (set automatically by asetup) |
| `STATANA_IMPL_DIR`   | Additional directories to search for implementation files |
| `PRIMARY_IMPL`       | If set, only this implementation's results affect exit status |
