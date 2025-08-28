# Author: Miguel Marina <karel.capek.robotics@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 Capek System Safety & Robotic Solutions
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Author: Miguel Marina <karel.capek.robotics@gmail.com>

# Derived Maturity Table: (avg_confidence, avg_robustness) → maturity level
DERIVED_MATURITY_TABLE = {
    (1, 1): 1, (1, 2): 1, (1, 3): 1, (1, 4): 2, (1, 5): 2,
    (2, 2): 2, (2, 3): 2, (2, 4): 3, (2, 5): 3,
    (3, 3): 3, (3, 4): 3, (3, 5): 4,
    (4, 4): 4, (4, 5): 4,
    (5, 5): 5,
}

ASSURANCE_AGGREGATION_AND = {
    (1,1): 3,
    (1,2): 4, (2,2): 4,
    (1,3): 4, (2,3): 4, (3,3): 5,
    (1,4): 5, (2,4): 5, (3,4): 5, (4,4): 5,
    (1,5): 5, (2,5): 5, (3,5): 5, (4,5): 5, (5,5): 5
}

AND_DECOMPOSITION_TABLE = {
    3: [(1, 1)],
    4: [(1, 2), (2, 2), (1, 3), (2, 3)],
    5: [(1, 4), (2, 4), (3, 4), (4, 4),
        (1, 5), (2, 5), (3, 5), (4, 5), (5, 5)]
}

OR_DECOMPOSITION_TABLE = {
    1: [(5, 5)],
    2: [(4, 4)],
    3: [(3, 3)],
    4: [(2, 2)],
    5: [(1, 1)]
}


def calculate_validation_target(acceptance_rate,
                                exposure_given_hb,
                                uncontrollable_given_exposure,
                                severity_given_uncontrollable):
    """Wrapper to derive a validation target for risk assessments."""
    from .utils import derive_validation_target

    return derive_validation_target(
        acceptance_rate,
        exposure_given_hb,
        uncontrollable_given_exposure,
        severity_given_uncontrollable,
    )
    
def boolify(value, default):
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value) if value is not None else default
        
class AutoMLHelper:
    """
    Helper class for risk assessment computations.
    It encapsulates methods to:
      - Generate unique node IDs.
      - Update the unique ID counter based on a list of top events.
      - Round a value to the nearest half.
      - Discretize a continuous value into a level from 1 to 5.
      - Combine input values based on gate type.
      - Recursively calculate assurance (or maturity/rigor) values.
    """
    def __init__(self):
        self.unique_node_id_counter = 1

    def aggregate_clone_requirements(self, clone_node):
        """
        If the given node is a clone, then:
          - For each child in the original node, collect its safety requirements.
          - Gather safety goals from the clone's own parents and the original node's parents.
          - Link (i.e. add) these safety goals to each of the collected requirements.
        
        Returns a dictionary keyed by requirement key (its "id" if available, else its text)
        with each value containing:
             "req": the requirement dictionary,
             "linked_sgs": a set of safety goal strings.
        """
        # Only process if node is a clone
        if not clone_node.is_primary_instance and hasattr(clone_node, "original") and clone_node.original:
            aggregated = {}

            # 1. Collect requirements from each child of the original node.
            # (Assume that the safety requirements live on the base events.)
            children_reqs = []
            for child in clone_node.original.children:
                # You might want to further traverse children if needed; here we assume direct children.
                if hasattr(child, "safety_requirements") and child.safety_requirements:
                    children_reqs.extend(child.safety_requirements)
                else:
                    # Optionally, if child has its own children, traverse downward.
                    def collect_reqs(n):
                        reqs = []
                        if hasattr(n, "safety_requirements") and n.safety_requirements:
                            reqs.extend(n.safety_requirements)
                        for c in n.children:
                            reqs.extend(collect_reqs(c))
                        return reqs
                    children_reqs.extend(collect_reqs(child))
            
            # 2. Gather safety goals from the clone's immediate parents.
            clone_parent_goals = set()
            for parent in clone_node.parents:
                if parent.safety_goal_description and parent.safety_goal_description.strip():
                    clone_parent_goals.add(f"- {parent.safety_goal_description.strip()}")
                else:
                    clone_parent_goals.add(f"- {parent.name}")
            
            # 3. Also gather safety goals from the original node's immediate parents.
            original_parent_goals = set()
            for parent in clone_node.original.parents:
                if parent.safety_goal_description and parent.safety_goal_description.strip():
                    original_parent_goals.add(f"- {parent.safety_goal_description.strip()}")
                else:
                    original_parent_goals.add(f"- {parent.name}")
            
            # Union both sets.
            safety_goals = clone_parent_goals.union(original_parent_goals)
            print(f"DEBUG: For clone node {clone_node.unique_id}, clone_parent_goals={clone_parent_goals}, original_parent_goals={original_parent_goals}")

            # 4. For each collected requirement, add the safety goals.
            for req in children_reqs:
                key = req.get("id") if req.get("id") else req.get("text", "Unnamed Requirement")
                if key not in aggregated:
                    aggregated[key] = {
                        "req": req,
                        "linked_sgs": set()
                    }
                aggregated[key]["linked_sgs"].update(safety_goals)
                print(f"DEBUG: Linking safety goals {safety_goals} to requirement {key} from original child")
            return aggregated
        else:
            # If not a clone, return an empty dict (or handle as needed)
            return {}

    def fix_clone_references(self, root_nodes):
        # First pass: collect all primary nodes from every top event.
        primary_by_id = {}
        def collect_primary(node):
            if node.is_primary_instance:
                primary_by_id[node.unique_id] = node
                print(f"[DEBUG] Added primary node: id={node.unique_id}, name='{node.user_name}'")
            for child in node.children:
                collect_primary(child)
        for root in root_nodes:
            collect_primary(root)
        
        # Second pass: update all clones using the complete dictionary.
        def fix(node):
            if not node.is_primary_instance:
                orig_id = getattr(node, "_original_id", node.unique_id)
                print(f"[DEBUG] Fixing clone: id={node.unique_id}, _original_id={orig_id}")
                if orig_id in primary_by_id:
                    node.original = primary_by_id[orig_id]
                    print(f"[DEBUG] Clone {node.unique_id} now references primary node {node.original.unique_id}")
                else:
                    node.original = node
                    print(f"[DEBUG] No matching primary for clone {node.unique_id} with _original_id={orig_id}; using self")
            else:
                node.original = node
                print(f"[DEBUG] Primary node {node.unique_id} set to reference itself")
            for child in node.children:
                fix(child)
        for root in root_nodes:
            fix(root)

    def get_next_unique_id(self):
        uid = self.unique_node_id_counter
        self.unique_node_id_counter += 1
        return uid

    def update_unique_id_counter_for_top_events(self, top_events):
        def traverse(node):
            ids = [node.unique_id]
            for child in node.children:
                ids.extend(traverse(child))
            return ids
        all_ids = []
        for event in top_events:
            all_ids.extend(traverse(event))
        if all_ids:
            self.unique_node_id_counter = max(all_ids) + 1
        else:
            # No nodes yet. Start numbering from 1.
            self.unique_node_id_counter = 1

    def round_to_half(self, val):
        try:
            val = float(val)
        except Exception as e:
            print(f"Error converting {val} to float: {e}")
            val = 0.0
        return round(val * 2) / 2

    def discretize_level(self, val):
        #r = self.round_to_half(val)
        r = val
        if r < 1.5:
            return 1
        elif r < 2.5:
            return 2
        elif r < 3.5:
            return 3
        elif r < 4.5:
            return 4
        else:
            return 5

    def scale_severity(self, sev):
        """Map severity 1-3 to a 1-5 scale."""
        try:
            sev = float(sev)
        except Exception:
            sev = 3
        sev = max(1.0, min(3.0, sev))
        return (sev - 1) * 2 + 1

    def scale_controllability(self, cont):
        """Map controllability 1-3 to a 1-5 scale."""
        try:
            cont = float(cont)
        except Exception:
            cont = 3
        cont = max(1.0, min(3.0, cont))
        return (cont - 1) * 2 + 1

    def combine_values(self, values, gate_type):
        if not values:
            return 1.0
        if gate_type.upper() == "AND":
            prod = 1.0
            for v in values:
                prod *= (1 - v/5)
            return (1 - prod) * 5
        else:
            return sum(values) / len(values)

    def combine_rigor_or(self,values):
        # Using the reliability (complement-product) formula.
        prod = 1.0
        for v in values:
            prod *= (1 - v/5)
        return round((1 - prod) * 5, 2)
        
    def combine_rigor_and(self,values):
        return sum(values) / len(values)            
            
    def combine_generic_values(self, values, gate_type):
        if not values:
            return None
        gate_type = gate_type.upper()
        if gate_type == "AND":
            prod = 1.0
            for v in values:
                prod *= (1 - round(v/5, 2))
            return round((1 - prod) * 5, 2)
        else:
            return round(sum(values) / len(values), 2)

    def is_effectively_confidence(self,node):
        """
        Returns True if the node is either:
          - A base event with node_type "CONFIDENCE LEVEL", or
          - A gate (or similar) whose children are all effectively confidence.
        """
        if node.node_type.upper() == "CONFIDENCE LEVEL":
            return True
        if node.children and node.node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
            return all(self.is_effectively_confidence(child) for child in node.children)
        return False

    def is_effectively_robustness(self,node):
        """
        Returns True if the node is either:
          - A base event with node_type "ROBUSTNESS SCORE", or
          - A gate (or similar) whose children are all effectively robustness.
        """
        if node.node_type.upper() == "ROBUSTNESS SCORE":
            return True
        if node.children and node.node_type.upper() in ["GATE", "RIGOR LEVEL", "TOP EVENT"]:
            return all(self.is_effectively_robustness(child) for child in node.children)
        return False

    def aggregate_assurance_and(self,child_levels):
        """
        Combine a list of children’s Prototype Assurance Levels (PAL) for an AND gate,
        using pairwise lookups in ASSURANCE_AGGREGATION_AND.
        """
        if not child_levels:
            return 1
        current = child_levels[0]
        for next_val in child_levels[1:]:
            pair = tuple(sorted((current, next_val)))
            # If not found in the dict, fallback to max(...) or something:
            current = ASSURANCE_AGGREGATION_AND.get(pair, max(pair))
        return current

    def aggregate_assurance_or(self,child_levels):
        if not child_levels:
            return 1
        avg = sum(child_levels) // len(child_levels)
        return max(1, min(5, avg))

    def derive_assurance_from_base(self,conf_values, rob_values):
        """
        Given lists of confidence and robustness integers (each 1..5),
        compute a single 'inverted' Prototype Assurance Level (PAL) from 1..5,
        where low confidence/robustness inputs produce a high assurance value.
        """
        if not conf_values or not rob_values:
            return 1  # fallback
        # Compute the integer average for each
        avg_conf = round(sum(conf_values) / len(conf_values))
        avg_rob  = round(sum(rob_values) / len(rob_values))
        # Hard-coded 5×5 assurance matrix:
        assurance_matrix = [
          [5, 4, 4, 3, 3],  # Confidence = 1
          [4, 4, 3, 3, 2],  # Confidence = 2
          [4, 3, 3, 2, 2],  # Confidence = 3
          [3, 3, 2, 2, 1],  # Confidence = 4
          [3, 2, 2, 1, 1]   # Confidence = 5
        ]
        # Adjust indices (1 maps to index 0, etc.)
        c_idx = max(1, min(5, avg_conf)) - 1
        r_idx = max(1, min(5, avg_rob)) - 1
        return assurance_matrix[c_idx][r_idx]

    def get_highest_parent_severity_for_node(self, node, all_top_events):
        """
        Return the highest severity found among all ancestors of all instances
        (primary or clone) of 'node' across every top event in 'all_top_events'.
        If no ancestor has a valid severity, return 3 by default.
        """
        # 1) Identify the primary ID for the node
        primary_id = node.unique_id if node.is_primary_instance else node.original.unique_id

        # 2) Collect all instances (primary or clones) with that primary ID from all top events.
        instances = []
        def collect_instances(root):
            def walk(n):
                if n.is_primary_instance and n.unique_id == primary_id:
                    instances.append(n)
                elif (not n.is_primary_instance and n.original and 
                      n.original.unique_id == primary_id):
                    instances.append(n)
                for c in n.children:
                    walk(c)
            walk(root)
        for te in all_top_events:
            collect_instances(te)

        # 3) Traverse upward (using DFS) from each instance to find the maximum severity.
        visited = set()
        max_sev = 0
        def dfs_up(n):
            nonlocal max_sev
            if n in visited:
                return
            visited.add(n)
            if n.severity is not None:
                try:
                    s = int(n.severity)
                    if s > max_sev:
                        max_sev = s
                except:
                    pass
            for p in n.parents:
                dfs_up(p)
            # For clones, also check the original's parents.
            if (not n.is_primary_instance) and n.original and (n.original != n):
                for p2 in n.original.parents:
                    dfs_up(p2)
        for inst in instances:
            dfs_up(inst)
        return max_sev if max_sev > 0 else 3

    def aggregate_assurance_or_adjusted(self, child_levels):
        """
        For an OR gate, compute the average of the child levels and then invert the result using a 6 - average rule.
        For example, if the average child level is 4 (strong), then 6 - 4 = 2, meaning the overall assurance requirement is 2.
        Ensure the final value is between 1 and 5.
        """
        if not child_levels:
            return 1
        avg = sum(child_levels) / len(child_levels)
        inverted = 6 - avg
        return max(1, min(5, round(inverted)))

    def calculate_assurance_recursive(self, node, all_top_events, visited=None):
        if node is None:
            return 1
        if visited is None:
            visited = set()
        if node.unique_id in visited:
            return node.quant_value if node.quant_value is not None else 1
        visited.add(node.unique_id)
        t = node.node_type.upper()

        # --- Base Events ---
        if t == "CONFIDENCE LEVEL":
            cval = max(1, min(5, int(node.quant_value if node.quant_value is not None else 1)))
            node.quant_value = cval
            node.display_label = f"Confidence [{cval}]"
            node.detailed_equation = f"Base Confidence => {cval}"
            return cval
        if t == "ROBUSTNESS SCORE":
            rval = max(1, min(5, int(node.quant_value if node.quant_value is not None else 1)))
            node.quant_value = rval
            node.display_label = f"Robustness [{rval}]"
            node.detailed_equation = f"Base Robustness => {rval}"
            return rval

        if not node.children:
            fallback = max(1, min(5, int(node.quant_value if node.quant_value is not None else 1)))
            node.quant_value = fallback
            node.display_label = f"Node [{fallback}]"
            node.detailed_equation = f"No children => fallback value {fallback}"
            return fallback

        # Process all children recursively.
        for child in node.children:
            self.calculate_assurance_recursive(child, all_top_events, visited)

        # --- Separate children into base events and composite children ---
        base_values = []
        composite_values = []
        for child in node.children:
            ctype = child.node_type.upper()
            if ctype in ["CONFIDENCE LEVEL", "ROBUSTNESS SCORE"]:
                # Use the already computed quant_value (which is now the assurance value)
                base_values.append(max(1, min(5, int(child.quant_value))))
            else:
                composite_values.append(max(1, min(5, int(child.quant_value))))

        # For the base events, if present, compute the assurance using our inversion matrix.
        if base_values:
            # When only one type is present, we use the same list for both inputs.
            base_assurance = self.derive_assurance_from_base(base_values, base_values)
        else:
            base_assurance = None

        # For composite children, aggregate their assurance values using the appropriate gate rule.
        gate = (node.gate_type or "AND").upper()
        if composite_values:
            if gate == "AND":
                composite_assurance = self.aggregate_assurance_and(composite_values)
            elif gate == "OR":
                composite_assurance = self.aggregate_assurance_or_adjusted(composite_values)
            else:
                composite_assurance = None
        else:
            composite_assurance = None

        # Combine base assurance and composite assurance.
        if base_assurance is not None and composite_assurance is not None:
            combined = (base_assurance + composite_assurance) // 2
        elif base_assurance is not None:
            combined = base_assurance
        elif composite_assurance is not None:
            combined = composite_assurance
        else:
            combined = 1

        level_map = {1: "PAL1", 2: "PAL2", 3: "PAL3", 4: "PAL4", 5: "PAL5"}

        if node.node_type.upper() == "TOP EVENT":
            try:
                s_raw = float(node.severity)
            except (TypeError, ValueError):
                s_raw = 3
            s = self.scale_severity(s_raw)
            
            try:
                c_raw = float(node.controllability)
            except (TypeError, ValueError):
                c_raw = 3
            c = self.scale_controllability(c_raw)

            final = round((combined + s + c) / 3)
            final = max(1, min(5, final))
            node.quant_value = final
            node.display_label = f"Prototype Assurance Level (PAL) [{level_map[final]}]"
            node.detailed_equation = (
                f"Base Assurance from children = {base_assurance if base_assurance is not None else 'N/A'}\n"
                f"Composite Assurance from gates = {composite_assurance if composite_assurance is not None else 'N/A'}\n"
                f"Combined (average) = {combined}\n"
                f"Node Severity (TOP EVENT) = {s_raw} (scaled: {s})\n"
                f"Node Controllability = {c_raw} (scaled: {c})\n"
                f"Final Assurance = (({combined} + {s} + {c}) /3) = {final}"
            )
            return final
        else:
            node.quant_value = combined
            node.display_label = f"Prototype Assurance Level (PAL) [{level_map[combined]}]"
            node.detailed_equation = (
                f"Base Assurance from children = {base_assurance if base_assurance is not None else 'N/A'}\n"
                f"Composite Assurance from gates = {composite_assurance if composite_assurance is not None else 'N/A'}\n"
                f"Combined Children Assurance (average) = {combined}\n"
            )
            return combined

    def calculate_probability_recursive(self, node, visited=None):
        """Return the probability of failure for ``node``.

        The method traverses the fault tree bottom-up, combining child
        probabilities according to the node's ``gate_type``.  For an AND gate
        the probabilities are multiplied, while an OR gate uses the
        ``1 - \u220f(1 - p)`` rule.  Basic events simply return their assigned
        probability.
        """
        if visited is None:
            visited = set()

        # Avoid infinite recursion but allow the same node to be evaluated
        # along different branches when it appears more than once.
        if node.unique_id in visited:
            return node.probability if node.probability is not None else 0.0

        visited.add(node.unique_id)
        t = node.node_type.upper()
        if t == "BASIC EVENT":
            prob = float(node.failure_prob)
            node.probability = prob
            node.display_label = f"P={prob:.2e}"
            return prob

        if not node.children:
            prob = float(getattr(node, "failure_prob", 0.0))
            node.probability = prob
            node.display_label = f"P={prob:.2e}"
            return prob

        # Use a fresh visited set for each child to ensure probabilities
        # propagate correctly even when subtrees are shared between gates.
        child_probs = [self.calculate_probability_recursive(c, visited.copy()) for c in node.children]

        gate = (node.gate_type or "AND").upper()
        if gate == "AND":
            prob = 1.0
            for p in child_probs:
                prob *= p
        else:
            prod = 1.0
            for p in child_probs:
                prod *= (1 - p)
            prob = 1 - prod
        node.probability = prob
        node.display_label = f"P={prob:.2e}"
        return prob



