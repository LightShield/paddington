"""Planning stage - converts optimization plans to source modifications."""

from typing import List
from ..stage import Stage
from ...struct_data.optimization_plan import OptimizationPlan
from ...struct_data.source_change import SourceModification, Modification, Location


class PlanningStage(Stage[List[OptimizationPlan], List[SourceModification]]):
    """Convert optimization plans to source modifications."""
    
    def __init__(self, access_modifier_strategy: str = "preserve"):
        self.access_modifier_strategy = access_modifier_strategy
    
    def process(self, plans: List[OptimizationPlan]) -> List[SourceModification]:
        """Create source modifications from plans."""
        modifications = []
        
        for plan in plans:
            if plan.skip_reason:
                continue
            
            if not plan.struct.file_path or not plan.struct.line:
                continue
            
            # Create modification for struct member reordering
            old_members = ", ".join(m.name for m in plan.original_order)
            new_members = ", ".join(m.name for m in plan.optimal_order)
            
            mod = Modification(
                type="reorder",
                location=Location(
                    file=plan.struct.file_path,
                    line=plan.struct.line,
                    column=0
                ),
                old_content=f"members: {old_members}",
                new_content=f"members: {new_members}",
                access_strategy=self.access_modifier_strategy
            )
            
            source_mod = SourceModification(
                file_path=plan.struct.file_path,
                struct_name=plan.struct.name,
                modifications=tuple([mod]),
                access_strategy=self.access_modifier_strategy
            )
            modifications.append(source_mod)
        
        return modifications
    
    def validate_input(self, plans: List[OptimizationPlan]) -> bool:
        """Validate input plans."""
        return isinstance(plans, list) and all(isinstance(p, OptimizationPlan) for p in plans)
