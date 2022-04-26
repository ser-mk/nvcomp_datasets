import os
import pprint
import ctypes
import sys
import importlib



def mock_compress(*args):
    return 200

class Compress:
    def __init__(self, path: str, debug=False):
        self.debug = debug
        if(self.debug):
            self._compress_api = mock_compress
            return
        self.comp_lib = ctypes.CDLL(path)

        self.comp_lib.test1.restype = ctypes.c_size_t
        self.comp_lib.test1.argtypes = [ctypes.c_int, ]
        self.test1 = self.comp_lib.test1

        self.comp_lib.test2.restype = None
        self.comp_lib.test2.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        self.test2 = self.comp_lib.test2

        self.comp_lib.nv_compress.restype = ctypes.c_size_t
        self.comp_lib.nv_compress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_bool, ctypes.c_int]

        self._compress_api = self.comp_lib.nv_compress


    class TestCase:
        def __init__(self, rle: int, delta: int, m2delta: bool, bp: int):
            self.rle = rle
            self.delta = delta
            self.m2delta = m2delta
            self.bp = bp
            self.result = None
            self.file_name = None
            self.bytes = None

        def __str__(self):
            return f"rle: {self.rle}, delta: {self.delta}, m2: {self.m2delta}, bp: {self.bp}"

        def case(self)-> str:
            return f"{self.rle}/{self.delta}/{self.bp}"

    def test(self):
        print('comp_lib.test(MortgageData2000): ', self.test1(1))
        print('comp_lib.test(2): ', self.test1(2))
        print('comp_lib.test(0): ', self.test1(0))
        print('comp_lib.test(0): ', self.test1(0))

        prt = (ctypes.c_uint16 * 4)(1, 2, 3, 4)
        self.test2(prt, 4)

        data = []
        for i in range(40):
            data.append(i%32)

        opt = self.TestCase(0, 1, True, 1)

        self._test_data(data)


    def _compress(self, data: list, bytes: int, opt: TestCase):
        d_types = {1: ctypes.c_uint8,
                   2: ctypes.c_uint16,
                   4: ctypes.c_uint32,
                   8: ctypes.c_uint64}
        lenthg = len(data)
        ptr = (d_types[bytes] * lenthg)(*data)
        # print(ptr)
        ret = self._compress_api(ptr, lenthg, bytes, opt.rle, opt.delta, opt.m2delta, opt.bp)
        # print("ret", ret)
        return ret


    def _var_compress(self, data: list, bytes: int)-> list:
        test_case_results = []
        for rle in range(0, 3):
            for delta in range(1, 4):
                for m2_delta in (True, False):
                    opt = self.TestCase(rle, delta, m2_delta, 1)
                    opt.result = self._compress(data, bytes, opt)
                    opt.bytes = bytes
                    test_case_results.append(opt)
        return test_case_results

    @staticmethod
    def _calc_bytes_compress(data: list)-> int:
        min_value = min(data)
        max_value = max(data)

        if abs(max_value) < abs(min_value):
            max_value = abs(min_value)

        if max_value < 127:
            return 1
        if max_value < 32767:
            return 2
        if max_value < 2147483647:
            return 4
        return 8

    def _test_data(self, data: list)-> list:
        bytes = self._calc_bytes_compress(data)
        test_case_results = self._var_compress(data, bytes)
        return test_case_results

    def _test_for_file(self, file_path: str)-> list:
        file_name = os.path.basename(file_path)
        import_file = file_name.split(".")[0]
        data_import = importlib.import_module('out.' + import_file)
        data = data_import.data
        test_case_results = self._test_data(data)
        return test_case_results


    def test_all_files(self)-> dict:
        d_test_case_results = {}
        for (root, dirs, files) in os.walk("out"):
            for file in files:
                test_case_results = self._test_for_file(file)
                d_test_case_results[file] = test_case_results
                self._show_stat(file, test_case_results)
        return d_test_case_results

    @staticmethod
    def _show_stat(name: str, test_case_results: list):
        d_test_case = {}
        for res in test_case_results:
            case_name = res.case()
            d_test_case[case_name] = {}
        for res in test_case_results:
            case_name = res.case()
            d_test_case[case_name][res.m2delta] = res.result
        print(f"{name} bytes: {res.bytes}")
        print("----"*33)
        for case, result in d_test_case.items():
            m2_result = result[True]
            commom_result = result[False]
            proc = (m2_result/commom_result)*100

            print(f"{case} : \t{m2_result}\t\t{commom_result}\t\t{proc:.2f}%")



path = "/content/1/lib/libcompress.so"


if len(sys.argv) > 1:
    path = sys.argv[1]
    print("path : ", path)

debug = False

compress = Compress(path, debug)

if debug:
    compress.test()

compress.test_all_files()
