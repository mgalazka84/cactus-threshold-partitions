"""Boundary, input-validation, and reconstruction checks."""
import unittest

from cactus_quorum import solve_cactus


class SolverTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(solve_cactus(0, []), (0, [], set()))

    def test_isolates(self):
        self.assertEqual(solve_cactus(4, [])[0], 4)

    def test_triangle_quorum(self):
        self.assertEqual(solve_cactus(3, [(0, 1), (1, 2), (2, 0)])[0], 1)

    def test_two_triangles(self):
        edges = [(0, 1), (1, 2), (2, 0), (0, 3), (3, 4), (4, 0)]
        optimum, parts, deleted = solve_cactus(5, edges)
        self.assertEqual(optimum, 2)
        self.assertEqual(sorted(v for p in parts for v in p), list(range(5)))
        self.assertTrue(deleted <= set(range(6)))

    def test_extreme_thresholds(self):
        edges = [(0, 1), (1, 2), (2, 0), (2, 3)]
        self.assertEqual(solve_cactus(5, edges, [0] * 5)[0], 5)
        self.assertEqual(solve_cactus(5, edges, [2, 2, 3, 1, 0])[0], 2)

    def test_iterable_inputs(self):
        self.assertEqual(solve_cactus(2, iter([(0, 1)]), iter([0, 0]))[0], 2)

    def test_invalid_graphs(self):
        bad = [(-1, []), (True, []), (2, [(0, 0)]), (2, [(0, 2)]),
               (2, [(0, 1), (1, 0)]), (2, [(0.0, 1)]),
               (4, [(0, 1), (1, 2), (2, 0), (0, 3), (1, 3)])]
        for n, edges in bad:
            with self.subTest(n=n, edges=edges), self.assertRaises(ValueError):
                solve_cactus(n, edges)

    def test_invalid_thresholds(self):
        for thresholds in ([0], [0, 2], [-1, 0], [0.5, 0], [True, 0]):
            with self.subTest(thresholds=thresholds), self.assertRaises(ValueError):
                solve_cactus(2, [(0, 1)], thresholds)

    def test_deep_path(self):
        n = 5001
        self.assertEqual(solve_cactus(n, [(i - 1, i) for i in range(1, n)])[0],
                         (n + 1) // 2)

    def test_long_cycle(self):
        n = 5001
        self.assertEqual(solve_cactus(n, [(i, (i + 1) % n) for i in range(n)])[0],
                         n // 2)


if __name__ == '__main__':
    unittest.main()
