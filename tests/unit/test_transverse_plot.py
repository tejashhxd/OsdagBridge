from osdagbridge.core.bridge_types.plate_girder.plot_generator import (
    DISP_MAP,
    FORCE_MAP,
    TRANSVERSE_MEMBERS_LABEL,
    build_figure_bmd,
    build_figure_deflection,
    build_figure_sfd,
)


class _Coordinate:
    def __init__(self, values):
        self.values = values


class _Slice:
    def __init__(self, values):
        self.values = values


class _ResultArray:
    def __init__(self, components, ids, values, id_name):
        self.coords = {
            "Component": _Coordinate(components),
            id_name: _Coordinate(ids),
        }
        self._values = values
        self._id_name = id_name

    def sel(self, **selection):
        component_index = self.coords["Component"].values.index(selection["Component"])
        ids = self.coords[self._id_name].values
        return _Slice([self._values[item][component_index] for item in ids])


def _transverse_plot_inputs():
    force_components = [component for pair in FORCE_MAP.values() for component in pair]
    force_values = {
        element: [0.0] * len(force_components)
        for element in (101, 102, 201, 202)
    }
    for component_i, component_j in FORCE_MAP.values():
        force_values[101][force_components.index(component_i)] = 1000.0
        force_values[101][force_components.index(component_j)] = 2000.0
        force_values[102][force_components.index(component_i)] = 3000.0
        force_values[102][force_components.index(component_j)] = 4000.0

    displacement_values = {
        node: [node / 1000.0] * len(DISP_MAP)
        for node in (1, 2, 3, 4)
    }
    dataset = {
        "forces": _ResultArray(
            force_components, [101, 102, 201, 202], force_values, "Element"
        ),
        "displacements": _ResultArray(
            ["x", "y", "z"], [1, 2, 3, 4], displacement_values, "Node"
        ),
    }
    nodes = {
        1: [0.0, 0.0, 0.0],
        2: [0.0, 0.0, 3.0],
        3: [5.0, 0.0, 0.0],
        4: [5.0, 0.0, 3.0],
    }
    members = {101: [1, 2], 102: [3, 4], 201: [1, 3], 202: [2, 4]}
    return dataset, nodes, members


def test_transverse_plot_supports_all_force_and_displacement_components():
    dataset, nodes, members = _transverse_plot_inputs()

    for key in FORCE_MAP:
        builder = build_figure_sfd if key.startswith("F") else build_figure_bmd
        figure, summary = builder(
            dataset,
            key,
            nodes,
            members,
            selected_girder=TRANSVERSE_MEMBERS_LABEL,
            transverse_members=[101, 102],
        )
        expected = {"min": -4.0, "max": 3.0} if key.startswith("F") else {
            "min": 1.0,
            "max": 4.0,
        }
        assert summary[TRANSVERSE_MEMBERS_LABEL] == expected
        figure.clear()

    for key in DISP_MAP:
        figure, summary = build_figure_deflection(
            dataset,
            key,
            nodes,
            members,
            selected_girder=TRANSVERSE_MEMBERS_LABEL,
            transverse_members=[101, 102],
        )
        expected = {"min": 1.0, "max": 4.0} if key == "Dx" else {
            "min": -4.0,
            "max": -1.0,
        }
        assert summary[TRANSVERSE_MEMBERS_LABEL] == expected
        figure.clear()
