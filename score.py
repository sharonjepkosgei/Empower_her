# -*- coding: utf-8 -*-
"""
Created on Thu Nov 30 23:24:06 2023

@author: ADMIN
"""

from girl import Girl
from placementcenter import PlacementCenter

def calculate_match_score(girl, center):
    # Adjust weights based on importance
    age_weight = 0.3
    services_weight = 0.3
    district_match_weight = 0.2

    # Direct district comparison
    district_match = 1 if girl.district == center.district else 0

    # Check if the girl's age is within the center's age range
    age_within_range = 1 if center.min_age <= girl.age <= center.max_age else 0

    # Calculate match score
    score = (
        district_match * district_match_weight +
        age_weight * age_within_range +
        len(set(girl.services_needed) & set(center.services_offered)) / len(girl.services_needed) * services_weight
    )

    return score



def find_best_placement(girl, centers):
    best_score = float('-inf')
    best_center = None

    for center in centers:
        # Calculate match score for each center
        score = calculate_match_score(girl, center)  

        # Update best center if the current score is higher
        if score > best_score:
            best_score = score
            best_center = center

    return best_center

