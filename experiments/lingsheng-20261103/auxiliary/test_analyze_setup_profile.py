import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('setup_analysis',HERE/'analyze_setup_profile.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class ExclusiveAttribution(unittest.TestCase):
    def test_real_old_flat_keeps_partition_and_exact_header(self):
        path=HERE.parent/'outputs/optimization-20261103/profile-hbw-evidence/rank00000.perf-flat.txt'
        data=module.parse_flat(path.read_text())
        self.assertEqual(data['total_lost_samples'],0)
        self.assertEqual(data['sample_count_header'],'23K')
        categories={name:0. for name in module.CATEGORIES}
        for row in data['rows']:categories[module.category(row)[0]]+=row['exclusive_percent']
        self.assertAlmostEqual(sum(categories.values()),data['shown_exclusive_percent'])
        self.assertGreater(categories['gomp_runtime'],40)
        self.assertGreater(categories['fine_sap_vcycle_work'],20)

    def test_inclusive_or_second_percent_column_rejected(self):
        for content in ["# Children Self\n# Samples: 10 of event 'cycles:u'\n10% 5% [.] foo", 
                        "# Samples: 10 of event 'cycles:u'\n10% 5% [.] foo"]:
            with self.assertRaises(ValueError):module.parse_flat(content)

    def test_symbol_only_report_does_not_invent_gomp_dso(self):
        data=module.parse_flat("# Samples: 1 of event 'cycles:u'\n 100.00% [.] 0x0000000000001e1b0\n")
        self.assertEqual(module.category(data['rows'][0])[0],'unresolved_symbol')
        self.assertIsNone(data['total_lost_samples'])

    def test_generate_basis_and_allocator_remain_ambiguous(self):
        for symbol,expected in [('NativeMG::generate_basis [clone ._omp_fn.1]','setup_shared_ambiguous'),
            ('std::_Rb_tree<unsigned long>::_M_emplace_hint_unique','memory_container_ambiguous')]:
            self.assertEqual(module.category(dict(symbol=symbol,dso='liblqcd_cpu.so',symbol_resolved=True))[0],expected)

    def test_std_vector_in_kernel_arguments_is_not_container_leaf(self):
        name='NativeMG::Impl::coarse_solve(std::vector<float> const&,std::vector<float>&)'
        self.assertEqual(module.category(dict(symbol=name,dso=None,symbol_resolved=True))[0],'coarse_solver_work')

    def test_multiple_events_rejected(self):
        content="# Samples: 1 of event 'cycles:u'\n100% [.] foo\n# Samples: 1 of event 'instructions:u'\n100% [.] foo"
        with self.assertRaises(ValueError):module.parse_flat(content)


if __name__=='__main__':unittest.main()
