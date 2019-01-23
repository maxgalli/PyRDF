import PyRDF, unittest, ROOT
from PyRDF import backend

def rangesToTuples(ranges):
    return map(lambda r: (r.start, r.end), ranges)

class DistBackendInitTest(unittest.TestCase):
    """
    Tests to ensure that the Dist abstract
    class cannot be instantiated.

    """
    def test_dist_init_error(self):
        """
        Test case to check that any attempt to
        instantiate the `Dist` abstract class
        results in a `TypeError`.

        """
        with self.assertRaises(TypeError):
            backend.Dist()

    def test_subclass_without_method_error(self):
        """
        Test case to check that creation of a
        subclass without implementing `processAndMerge`
        method throws a `TypeError`.

        """
        class TestBackend(backend.Dist):
            pass

        with self.assertRaises(TypeError):
            TestBackend()

class DistBuildRangesTest(unittest.TestCase):
    """
    Tests to check the working of the `BuildRanges`
    instance method in `Dist` class.

    """
    class TestBackend(backend.Dist):
        """
        A Dummy backend class to test the
        BuildRanges method in Dist class.

        """
        def ProcessAndMerge(self, mapper, reducer):
            """
            Dummy implementation of ProcessAndMerge.

            """
            pass

    def test_nentries_multipleOf_npartitions(self):
        """
        Test cases that check the working of `BuildRanges`
        method when `nentries` is a multiple of `npartitions`.

        """
        backend = DistBuildRangesTest.TestBackend()
        nentries_small = 10
        npartitions_small = 5
        nentries_large = 100
        npartitions_large = 10

        ranges_small = rangesToTuples(backend._getBalancedRanges(nentries_small, npartitions_small))
        ranges_large = rangesToTuples(backend._getBalancedRanges(nentries_large, npartitions_large))

        ranges_small_reqd = [(0, 2), (2, 4), (4, 6), (6, 8), (8, 10)]
        ranges_large_reqd = [
        (0, 10),
        (10, 20),
        (20, 30),
        (30, 40),
        (40, 50),
        (50, 60),
        (60, 70),
        (70, 80),
        (80, 90),
        (90, 100)
        ]

        self.assertListEqual(ranges_small, ranges_small_reqd)
        self.assertListEqual(ranges_large, ranges_large_reqd)

    def test_nentries_not_multipleOf_npartitions(self):
        """
        Test cases that check the working of `BuildRanges` method
        when `nentries` is not a multiple of `npartitions`.

        """
        backend = DistBuildRangesTest.TestBackend()
        nentries_1 = 10
        npartitions_1 = 4
        nentries_2 = 9
        npartitions_2 = 4

        # Example in which fractional part of
        # (nentries/npartitions) >= 0.5
        ranges_1 = rangesToTuples(backend._getBalancedRanges(nentries_1, npartitions_1))
        # Example in which fractional part of
        # (nentries/npartitions) < 0.5
        ranges_2 = rangesToTuples(backend._getBalancedRanges(nentries_2, npartitions_2))

        # Required output pairs
        ranges_1_reqd = [(0, 3), (3, 6), (6, 8), (8, 10)]
        ranges_2_reqd = [(0, 3), (3, 5), (5, 7), (7, 9)]

        self.assertListEqual(ranges_1, ranges_1_reqd)
        self.assertListEqual(ranges_2, ranges_2_reqd)

    def test_nentries_greater_than_npartitions(self):
        """
        Test case that check the working of `BuildRanges` method
        when the value of `nentries` is lesser than `npartitions`.

        """
        backend = DistBuildRangesTest.TestBackend()
        nentries = 5
        npartitions = 7 # > nentries

        ranges = rangesToTuples(backend._getBalancedRanges(nentries, npartitions))

        ranges_reqd = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]

        self.assertListEqual(ranges, ranges_reqd)

    def test_clustered_ranges_with_one_cluster(self):
        """
        Check that _getClusteredRanges returns one range when the dataset
        contains a single cluster and the number of partitions is 1

        """
        backend = DistBuildRangesTest.TestBackend()
        treename = "TotemNtuple"
        filelist = ["tests/unit/backend/Slimmed_ntuple.root"]
        nentries = 10
        npartitions = 1

        crs = backend._getClusteredRanges(nentries, npartitions, treename, filelist)
        ranges = rangesToTuples(crs)

        ranges_reqd = [(0L, 10L)]

        self.assertListEqual(ranges, ranges_reqd)

    def test_warning_in_clustered_ranges_npartitions_greater_than_clusters(self):
        """
        Check that _getClusteredRanges raises a warning when the number of
        partitions is bigger than the number of clusters in the dataset.

        """
        import warnings

        backend = DistBuildRangesTest.TestBackend()
        treename = "TotemNtuple"
        filelist = ["tests/unit/backend/Slimmed_ntuple.root"]
        nentries = 10
        npartitions = 2

        ranges_reqd = [(0L, 10L)]

        with warnings.catch_warnings(record=True) as w:
            # Trigger warning
            crs = backend._getClusteredRanges(nentries, npartitions, treename, filelist)
            ranges = rangesToTuples(crs)

            # Verify ranges
            self.assertListEqual(ranges, ranges_reqd)

            # Verify warning
            assert issubclass(w[-1].category, UserWarning)

    def test_clustered_ranges_with_two_clusters_two_partitions(self):
        """
        Check that _getClusteredRanges creates clustered ranges respecting
        the cluster boundaries even if that implies to have ranges with very
        different numbers of entries.

        """
        backend = DistBuildRangesTest.TestBackend()
        treename = "DataSet/TestA1.cel"
        filelist = ["tests/unit/backend/2clusters.root"]
        nentries = 1000
        npartitions = 2

        crs = backend._getClusteredRanges(nentries, npartitions, treename, filelist)
        ranges = rangesToTuples(crs)

        ranges_reqd = [
            (0L,     15875L),
            (15875L, 15876L)
        ]

        self.assertListEqual(ranges, ranges_reqd)

    def test_clustered_ranges_with_many_clusters_four_partitions(self):
        """
        Check that _getClusteredRanges creates clustered ranges as equal as
        possible for four partitions

        """
        backend = DistBuildRangesTest.TestBackend()
        treename = "myTree"
        filelist = ["tests/unit/backend/1000clusters.root"]
        nentries = 1000
        npartitions = 4

        crs = backend._getClusteredRanges(nentries, npartitions, treename, filelist)
        ranges = rangesToTuples(crs)

        ranges_reqd = [
            (0L,   250L),
            (250L, 500L),
            (500L, 750L),
            (750L, 1000L)
        ]

        self.assertListEqual(ranges, ranges_reqd)

    def test_clustered_ranges_with_many_clusters_many_partitions(self):
        """
        Check that _getClusteredRanges creates clustered ranges as equal as
        possible for the maximum number of possible partitions (number of
        clusters)

        """
        backend = DistBuildRangesTest.TestBackend()
        treename = "myTree"
        filelist = ["tests/unit/backend/1000clusters.root"]
        nentries = 1000
        npartitions = 1000

        crs = backend._getClusteredRanges(nentries, npartitions, treename, filelist)
        ranges = rangesToTuples(crs)

        start = 0
        end = 1000
        step = 1

        ranges_reqd = [ (a,b) for a,b in zip(range(start, end, step), range(step, end+1, step)) ]

        self.assertListEqual(ranges, ranges_reqd)

    def test_buildranges_with_clustered_ranges(self):
        """
        Check that BuildRanges produces clustered ranges when the dataset
        contains clusters.

        """
        backend = DistBuildRangesTest.TestBackend()

        # Mock attributes accessed through self. inside BuildRanges
        backend.treename = "myTree"
        backend.files = "tests/unit/backend/1000clusters.root"
        backend.nentries = 1000
        npartitions = 1000

        crs = backend.BuildRanges(npartitions)
        ranges = rangesToTuples(crs)

        start = 0
        end = 1000
        step = 1

        ranges_reqd = [ (a,b) for a,b in zip(range(start, end, step), range(step, end+1, step)) ]

        self.assertListEqual(ranges, ranges_reqd)

    def test_buildranges_with_balanced_ranges(self):
        """
        Check that BuildRanges produces balanced ranges when there are no
        clusters involved.

        """
        backend = DistBuildRangesTest.TestBackend()

        # Mock attributes accessed through self. inside BuildRanges
        backend.nentries = 50
        npartitions = 16

        crs = backend.BuildRanges(npartitions)
        ranges = rangesToTuples(crs)

        ranges_reqd = [
            (0,  4) , (4,  8) , (8,  11), (11, 14), (14, 17), (17, 20),
            (20, 23), (23, 26), (26, 29), (29, 32), (32, 35), (35, 38),
            (38, 41), (41, 44), (44, 47), (47, 50)
        ]

        self.assertListEqual(ranges, ranges_reqd)
