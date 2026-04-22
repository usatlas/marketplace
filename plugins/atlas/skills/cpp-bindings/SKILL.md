---
name: cpp-bindings
description: >-
  Use when writing Python bindings for C++ HEP code with nanobind or pybind11:
  exposing a C++ class or function to Python, binding STL containers (vector,
  map), handling numpy/awkward array interop, choosing between nanobind and
  pybind11, or setting up a CMake build that produces a Python extension module.
---

# C++ Python Bindings (nanobind / pybind11)

## Overview

nanobind and pybind11 are C++ header-only libraries for creating Python
extension modules from C++ code. pybind11 is the established standard; nanobind
is a leaner, faster successor from the same author (Wenzel Jakob) designed for
Python 3.8+ and offering smaller binary size and faster compile times. In HEP,
bindings are used to expose ROOT-based code, custom reconstruction algorithms,
or legacy C++ analysis code to Python without rewriting.

## Choosing Between nanobind and pybind11

| Feature       | nanobind                             | pybind11            |
| ------------- | ------------------------------------ | ------------------- |
| Compile time  | Faster (30–50%)                      | Slower              |
| Binary size   | Smaller                              | Larger              |
| STL bindings  | Opaque by default                    | Transparent         |
| ABI stability | Guaranteed between nanobind versions | No guarantee        |
| Maturity      | Newer (2022+)                        | Very mature (2015+) |
| Documentation | Growing                              | Comprehensive       |

**Recommendation**: Use **nanobind** for new projects. Use **pybind11** when
integrating with existing pybind11-based code or when you need the larger
ecosystem of pybind11 extensions.

## CMake Setup

### nanobind

```cmake
cmake_minimum_required(VERSION 3.15)
project(myhep)

find_package(Python 3.8 COMPONENTS Interpreter Development.Module REQUIRED)
find_package(nanobind CONFIG REQUIRED)

nanobind_add_module(myhep_ext myhep.cpp)
target_link_libraries(myhep_ext PRIVATE MyHEPLib)
```

### pybind11

```cmake
find_package(pybind11 CONFIG REQUIRED)
pybind11_add_module(myhep_ext myhep.cpp)
target_link_libraries(myhep_ext PRIVATE MyHEPLib)
```

## Canonical Patterns

### Bind a simple function (nanobind)

```cpp
// myhep.cpp
#include <nanobind/nanobind.h>

namespace nb = nanobind;

double invariant_mass(double px, double py, double pz, double e) {
    double m2 = e*e - px*px - py*py - pz*pz;
    return m2 > 0.0 ? std::sqrt(m2) : 0.0;
}

NB_MODULE(myhep_ext, m) {
    m.def("invariant_mass", &invariant_mass,
          nb::arg("px"), nb::arg("py"), nb::arg("pz"), nb::arg("e"),
          "Compute invariant mass from four-momentum (GeV).");
}
```

```python
import myhep_ext
m = myhep_ext.invariant_mass(0.0, 0.0, 0.0, 125.0)  # → 125.0 GeV
```

### Bind a class (nanobind)

```cpp
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>

namespace nb = nanobind;

class Jet {
public:
    Jet(double pt, double eta, double phi) : pt_(pt), eta_(eta), phi_(phi) {}
    double pt() const { return pt_; }
    double eta() const { return eta_; }
    std::string repr() const {
        return "Jet(pt=" + std::to_string(pt_) + ")";
    }
private:
    double pt_, eta_, phi_;
};

NB_MODULE(myhep_ext, m) {
    nb::class_<Jet>(m, "Jet")
        .def(nb::init<double, double, double>(),
             nb::arg("pt"), nb::arg("eta"), nb::arg("phi"))
        .def("pt",  &Jet::pt)
        .def("eta", &Jet::eta)
        .def("__repr__", &Jet::repr);
}
```

### numpy array interop (nanobind)

```cpp
#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>

namespace nb = nanobind;
using Array1D = nb::ndarray<double, nb::shape<-1>, nb::c_contig>;

nb::ndarray<double, nb::ndim<1>, nb::c_contig>
compute_pt(Array1D px, Array1D py) {
    size_t n = px.shape(0);
    auto result = new double[n];
    for (size_t i = 0; i < n; ++i)
        result[i] = std::sqrt(px(i)*px(i) + py(i)*py(i));
    nb::capsule owner(result, [](void *p) noexcept { delete[] (double*)p; });
    return nb::ndarray<double, nb::ndim<1>, nb::c_contig>(result, {n}, owner);
}

NB_MODULE(myhep_ext, m) {
    m.def("compute_pt", &compute_pt);
}
```

### STL containers (pybind11)

```cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>   // auto-converts std::vector ↔ list

namespace py = pybind11;

std::vector<double> jet_pts(std::vector<double> px, std::vector<double> py) {
    std::vector<double> result;
    for (size_t i = 0; i < px.size(); ++i)
        result.push_back(std::sqrt(px[i]*px[i] + py[i]*py[i]));
    return result;
}

PYBIND11_MODULE(myhep_ext, m) {
    m.def("jet_pts", &jet_pts);
}
```

## Gotchas

- **GIL (Global Interpreter Lock)**: For CPU-bound C++ functions that don't
  touch Python objects, release the GIL with `nb::gil_scoped_release` to allow
  parallel Python threads.
- **Lifetime management**: Python's garbage collector doesn't know about C++
  object lifetimes. Use `nb::keep_alive` or `py::keep_alive` policies for
  objects that hold references.
- **STL opaque types in nanobind**: nanobind does NOT auto-convert `std::vector`
  to Python lists by default (unlike pybind11). Include
  `<nanobind/stl/vector.h>` to enable conversion.
- **ROOT dictionary conflicts**: When linking against ROOT, ROOT's
  auto-generated dictionaries may conflict with pybind11/nanobind. Use a
  separate shared library to isolate ROOT from the Python extension.
- **ABI mismatch**: The Python extension must be compiled against the same
  Python version and ABI as the interpreter. Use `scikit-build-core` or
  `meson-python` to manage this.

## Interop

- **numpy**: `<nanobind/ndarray.h>` (nanobind) or `<pybind11/numpy.h>`
  (pybind11) for zero-copy array passing.
- **awkward**: awkward's `ak.from_buffers` / `ak.to_buffers` can wrap C++
  arrays; combine with nanobind ndarray for zero-copy workflows.
- **CMake + scikit-build-core**: The recommended build backend for Python
  extensions that use CMake.

## Docs

nanobind: https://nanobind.readthedocs.io/ pybind11:
https://pybind11.readthedocs.io/
