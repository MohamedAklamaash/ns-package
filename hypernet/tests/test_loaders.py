import pytest

from hypernet.config import data_root
from hypernet.io import load_house_committees, load_senate_committees

pytestmark = pytest.mark.skipif(not data_root().exists(), reason="data root missing")


@pytest.mark.parametrize(
    "loader,nodes,edges",
    [
        (load_house_committees, 1290, 341),
        (load_senate_committees, 282, 315),
    ],
)
def test_congress(loader, nodes, edges):
    hg, labels = loader()
    assert (hg.num_nodes, hg.num_edges) == (nodes, edges)
    assert set(labels.tolist()) == {0, 1}
    assert labels.min() == 0 and hg.node_labels is labels
