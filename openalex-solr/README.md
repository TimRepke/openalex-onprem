
```bash
cd openalex-solr
python setup.py build_ext --inplace
python msg.py
```



 c++ -O3 -Wall  -shared -Iinclude -fPIC $(python3 -m pybind11 --includes) -std=c++11 test.cpp -o test$(python3-config --extension-suffix)
 


 c++ -O3 -Wall  -shared -Iinclude -std=c++11 invert.cpp -o invert