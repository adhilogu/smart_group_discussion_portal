"""def calculate_group_voting_with_bias_detection():
    # Initialize Group A members
    group_a = ["A1", "A2", "A3", "A4", "A5"]

    # CONFIGURABLE PARAMETERS
    BIAS_PENALTY = -1  # Penalty points for biased voting
    DEVIATION_THRESHOLD = 2  # Maximum allowed deviation from median
    ABSENCE_PENALTY = -10  # Penalty for not participating in a question

    # Track attendance for each question
    attendance = {q: set() for q in range(1, 11)}

    # Initialize question-wise scores dictionary
    question_scores = {q: {member: 0 for member in group_a} for q in range(1, 11)}

    # Initialize total scores before penalties
    raw_scores = {member: 0 for member in group_a}

    # Initialize bias penalties for each voter
    bias_penalties = {member: 0 for member in group_a}

    # Initialize absence penalties for each member
    absence_penalties = {member: 0 for member in group_a}

    # Initialize bias detection records
    bias_records = {q: [] for q in range(1, 11)}

    # Simulated voting data
    simulated_votes = {
        'A1': {
            1: {1: 'A5', 2: 'A4', 3: 'A2'},
            2: {1: 'A5', 2: 'A4', 3: 'A2'},
            3: {1: 'A3', 2: 'A4', 3: 'A2'},  # BIAS: A3 gets rank 1 when others give rank 3 or 0
            4: {1: 'A5', 2: 'A4', 3: 'A2'},
            5: {1: 'A5', 2: 'A4', 3: 'A2'},
            6: {1: 'A5', 2: 'A2', 3: 'A4'},
            7: {1: 'A2', 2: 'A5', 3: 'A4'},
            8: {1: 'A4', 2: 'A5', 3: 'A2'},
            9: {1: 'A2', 2: 'A5', 3: 'A4'},
            10: {1: 'A5', 2: 'A2', 3: 'A4'}
        },
        'A2': {
            1: {1: 'A4', 2: 'A3', 3: 'A5'},
            2: {1: 'A3', 2: 'A5', 3: 'A1'},
            3: {1: 'A5', 2: 'A4', 3: 'A3'},  # A3 gets rank 3 (matches consensus)
            4: {1: 'A5', 2: 'A3', 3: 'A1'},
            5: {1: 'A4', 2: 'A5', 3: 'A1'},
            6: {1: 'A1', 2: 'A5', 3: 'A4'},
            7: {1: 'A3', 2: 'A5', 3: 'A1'},
            8: {1: 'A4', 2: 'A1', 3: 'A5'},
            9: {1: 'A5', 2: 'A3', 3: 'A1'},
            10: {1: 'A1', 2: 'A4', 3: 'A3'}
        },
        'A3': {
            1: {1: 'A5', 2: 'A4', 3: 'A2'},
            2: {1: 'A2', 2: 'A5', 3: 'A4'},
            3: {1: 'A5', 2: 'A2', 3: 'A4'},  # No vote for A3 (self)

            5: {1: 'A5', 2: 'A2', 3: 'A4'},
            6: {1: 'A5', 2: 'A2', 3: 'A4'},
            7: {1: 'A5', 2: 'A2', 3: 'A4'},
            8: {1: 'A5', 2: 'A2', 3: 'A4'},
            9: {1: 'A2', 2: 'A5', 3: 'A4'},
            10: {1: 'A2', 2: 'A5', 3: 'A4'}
        },
        'A4': {
            1: {1: 'A1', 2: 'A3', 3: 'A5'},
            2: {1: 'A5', 2: 'A2', 3: 'A3'},
            3: {1: 'A2', 2: 'A1', 3: 'A3'},  # A3 gets rank 3 (matches consensus)
            4: {1: 'A3', 2: 'A5', 3: 'A1'},
            5: {1: 'A1', 2: 'A3', 3: 'A2'},
            6: {1: 'A2', 2: 'A5', 3: 'A3'},
            7: {1: 'A3', 2: 'A1', 3: 'A5'},
            8: {1: 'A5', 2: 'A2', 3: 'A1'},
            9: {1: 'A1', 2: 'A3', 3: 'A2'},
            10: {1: 'A2', 2: 'A5', 3: 'A1'}
        },
        'A5': {
            1: {1: 'A2', 2: 'A4', 3: 'A1'},
            2: {1: 'A2', 2: 'A4', 3: 'A3'},
            3: {1: 'A4', 2: 'A2', 3: 'A3'},  # A3 gets rank 3 (matches consensus)
            4: {1: 'A4', 2: 'A2', 3: 'A3'},
            5: {1: 'A2', 2: 'A4', 3: 'A3'},
            6: {1: 'A3', 2: 'A2', 3: 'A4'},
            7: {1: 'A4', 2: 'A2', 3: 'A3'},
            8: {1: 'A2', 2: 'A4', 3: 'A3'},
            9: {1: 'A4', 2: 'A2', 3: 'A3'},
            10: {1: 'A2', 2: 'A4', 3: 'A3'}
        }
    }

    # Process votes for each question separately
    for question in range(1, 11):
        # Record attendance
        for voter in simulated_votes:
            if question in simulated_votes[voter]:
                attendance[question].add(voter)

        # Apply absence penalties
        for member in group_a:
            if member not in attendance[question]:
                absence_penalties[member] += ABSENCE_PENALTY
                bias_records[question].append({
                    "voter": member,
                    "absence": True,
                    "penalty": ABSENCE_PENALTY
                })

        # Track ranks given to each member for this question
        member_ranks = {member: [] for member in group_a}

        # Collect all ranks for each member for this question
        for voter in attendance[question]:
            vote_data = simulated_votes[voter][question]

            # Record which members received votes and their ranks
            voted_members = {}
            for rank, recipient in vote_data.items():
                if recipient != voter:  # Skip self-votes
                    voted_members[recipient] = rank

            # Record ranks (or default rank 4 for non-ranked members)
            for member in group_a:
                if member != voter:  # Skip self
                    rank = voted_members.get(member, 4)  # Rank 4 = 0 marks (not ranked)
                    member_ranks[member].append((voter, rank))

        # Calculate the median rank for each member (to identify outliers)
        median_ranks = {}
        for member, ranks in member_ranks.items():
            if ranks:
                just_ranks = [r for _, r in ranks]
                median_ranks[member] = sorted(just_ranks)[len(just_ranks) // 2]

        # First calculate scores without checking for bias
        for member in group_a:
            for voter, rank in member_ranks[member]:
                # Calculate marks (Rank 1 = 3 marks, Rank 2 = 2 marks, Rank 3 = 1 mark, Rank 4 = 0 marks)
                marks = max(4 - rank, 0)

                # Add to question scores and raw scores
                question_scores[question][member] += marks
                raw_scores[member] += marks

        # Now check for bias and apply penalties to the VOTER (not recipient)
        for member in group_a:
            for voter, rank in member_ranks[member]:
                # Check for bias - if rank deviates more than threshold from median
                if abs(rank - median_ranks[member]) > DEVIATION_THRESHOLD:
                    # Apply penalty to the voter (not the recipient)
                    bias_penalties[voter] += BIAS_PENALTY

                    # Record the bias instance
                    bias_records[question].append({
                        "voter": voter,
                        "recipient": member,
                        "given_rank": rank,
                        "median_rank": median_ranks[member],
                        "deviation": abs(rank - median_ranks[member]),
                        "penalty": BIAS_PENALTY
                    })

    # Calculate final scores after penalties
    final_scores = {}
    for member in group_a:
        final_scores[member] = raw_scores[member] + bias_penalties[member] + absence_penalties[member]

    return question_scores, raw_scores, final_scores, bias_penalties, absence_penalties, bias_records


# Run the simulation
question_scores, raw_scores, final_scores, bias_penalties, absence_penalties, bias_records = calculate_group_voting_with_bias_detection()

# Define group members for output
group_a = ["A1", "A2", "A3", "A4", "A5"]

# Display results for each question
for question in range(1, 11):
    print(f"\n===== QUESTION {question} =====")

    # Show scores for this question
    print(f"\nScores for Question {question}:")
    for member in group_a:
        print(f"{member}: {question_scores[question][member]} marks")

    # Show bias instances for this question
    bias_instances = [record for record in bias_records[question] if 'absence' not in record]
    if bias_instances:
        print(f"\nBias detected in Question {question}:")
        for record in bias_instances:
            print(f"  {record['voter']} gave {record['recipient']} rank {record['given_rank']} "
                  f"(median: {record['median_rank']}, deviation: {record['deviation']}, penalty to voter: {record['penalty']})")
    else:
        print(f"\nNo bias detected in Question {question}")

# Display final results
print("\n===== OVERALL RESULTS =====")
print("\nRaw scores before penalties:")
for member, score in sorted(raw_scores.items()):
    print(f"{member}: {score} marks")

print("\nBias penalties (applied to the biased voter):")
for member, penalty in sorted(bias_penalties.items()):
    print(f"{member}: {penalty} penalty marks")

print("\nAbsence penalties:")
for member, penalty in sorted(absence_penalties.items()):
    print(f"{member}: {penalty} penalty marks")

print("\nFinal scores after all penalties:")
for member, score in sorted(final_scores.items()):
    print(f"{member}: {score} marks")
    print(f"  Raw score: {raw_scores[member]}")
    print(f"  Bias penalty: {bias_penalties[member]}")
    print(f"  Absence penalty: {absence_penalties[member]}")
    print(f"  Total: {raw_scores[member]} + {bias_penalties[member]} + {absence_penalties[member]} = {score}")"""

import numpy as np
from collections import defaultdict


def calculate_group_voting_with_mean_threshold(group_members, simulated_votes):
    """
    Calculate group voting with bias detection based on mean score approach.

    Parameters:
    group_members (list): List of group member identifiers
    simulated_votes (dict): Voting data for all members

    Returns:
    tuple: Multiple results including scores, penalties, and voting records
    """
    # Configure ranking system based on group size
    num_members = len(group_members)

    # Determine number of ranks based on group size
    if num_members < 6:
        raise ValueError("Group size must be at least 6 members")
    elif 6 <= num_members <= 11:
        max_ranks = 2
    elif 12 <= num_members <= 17:
        max_ranks = 3
    elif 18 <= num_members <= 23:
        max_ranks = 4
    elif 24 <= num_members <= 29:
        max_ranks = 5
    else:
        raise ValueError("Group size must not exceed 29 members")

    # Score for each rank (rank i gets max_ranks+1-i points)
    rank_scores = {i: max_ranks + 1 - i for i in range(1, max_ranks + 1)}

    # Calculate parameters based on requirements
    HIGHEST_RANK_SCORE = rank_scores[1]
    BIAS_PENALTY = -HIGHEST_RANK_SCORE
    ABSENCE_PENALTY = -(HIGHEST_RANK_SCORE * num_members)

    # Default threshold - this will be adjusted per question and member
    BASE_THRESHOLD = max_ranks / 3

    # Print parameters before calculation
    print("\n===== VOTING SYSTEM PARAMETERS =====")
    print(f"Group Size: {num_members} members")
    print(f"Maximum Ranks Allowed: {max_ranks}")
    print(f"Rank Scores: {', '.join([f'Rank {i}: {rank_scores[i]} marks' for i in range(1, max_ranks + 1)])}")
    print(f"Base Threshold: ±{BASE_THRESHOLD} (will be adjusted per question)")
    print(f"Bias Penalty: {BIAS_PENALTY} marks")
    print(f"Absence Penalty: {ABSENCE_PENALTY} marks")
    print("=====================================\n")

    # Track attendance for each question
    attendance = {q: set() for q in range(1, 11)}

    # Initialize question-wise scores dictionary
    question_scores = {q: {member: 0 for member in group_members} for q in range(1, 11)}

    # Initialize voting record (who voted for whom)
    voting_record = {q: {voter: {recipient: 0 for recipient in group_members if recipient != voter}
                         for voter in group_members} for q in range(1, 11)}

    # Initialize total scores before penalties
    raw_scores = {member: 0 for member in group_members}

    # Initialize bias penalties for each voter for each question
    bias_penalties_by_question = {q: {member: 0 for member in group_members} for q in range(1, 11)}

    # Initialize absence penalties for each member for each question
    absence_penalties_by_question = {q: {member: 0 for member in group_members} for q in range(1, 11)}

    # Initialize bias detection records
    bias_records = {q: [] for q in range(1, 11)}

    # Track thresholds and means by question and member
    question_member_means = {q: {} for q in range(1, 11)}
    question_member_thresholds = {q: {} for q in range(1, 11)}

    # Process votes for each question separately
    for question in range(1, 11):
        # Record attendance
        for voter in group_members:
            if voter in simulated_votes and question in simulated_votes[voter]:
                attendance[question].add(voter)
            else:
                # Apply absence penalties
                absence_penalties_by_question[question][voter] = ABSENCE_PENALTY
                bias_records[question].append({
                    "voter": voter,
                    "absence": True,
                    "penalty": ABSENCE_PENALTY
                })

        # Track ranks and scores given to each member for this question
        member_ranks = {member: [] for member in group_members}
        member_scores = {member: [] for member in group_members}

        # Collect all ranks and convert to scores for each member
        for voter in attendance[question]:
            vote_data = simulated_votes[voter][question]

            # Record which members received votes and their ranks/scores
            for rank, recipient in vote_data.items():
                if recipient != voter and recipient in group_members:  # Skip self-votes
                    # Only process valid ranks
                    if 1 <= rank <= max_ranks:
                        # Convert rank to score
                        score = rank_scores.get(rank, 0)

                        # Record rank and score
                        member_ranks[recipient].append(rank)
                        member_scores[recipient].append(score)

                        # Store in voting record
                        voting_record[question][voter][recipient] = score

        # Calculate mean score and threshold for each member
        for member in group_members:
            if member_scores[member]:
                # Calculate mean score for this member for this question
                mean_score = sum(member_scores[member]) / len(member_scores[member])
                question_member_means[question][member] = mean_score

                # Calculate threshold as a function of the range of possible scores
                score_range = max(rank_scores.values()) - min(rank_scores.values())
                threshold = score_range / 3
                question_member_thresholds[question][member] = threshold

        # First calculate raw scores without checking for bias
        for voter in attendance[question]:
            vote_data = simulated_votes[voter][question]

            for rank, recipient in vote_data.items():
                if recipient != voter and recipient in group_members:
                    if 1 <= rank <= max_ranks:
                        score = rank_scores.get(rank, 0)
                        question_scores[question][recipient] += score
                        raw_scores[recipient] += score

        # Now check for bias using mean-based threshold
        for voter in attendance[question]:
            vote_data = simulated_votes[voter][question]

            for rank, recipient in vote_data.items():
                if recipient != voter and recipient in group_members:
                    if 1 <= rank <= max_ranks:
                        # Get the mean score and threshold for this recipient
                        if recipient in question_member_means[question]:
                            mean_score = question_member_means[question][recipient]
                            threshold = question_member_thresholds[question][recipient]

                            # Convert voter's rank to score
                            given_score = rank_scores.get(rank, 0)

                            # Check if the score is outside the acceptable range
                            if abs(given_score - mean_score) > threshold:
                                # Apply bias penalty to the voter
                                bias_penalties_by_question[question][voter] += BIAS_PENALTY

                                # Record the bias instance
                                bias_records[question].append({
                                    "voter": voter,
                                    "recipient": recipient,
                                    "given_rank": rank,
                                    "given_score": given_score,
                                    "mean_score": mean_score,
                                    "threshold": threshold,
                                    "deviation": abs(given_score - mean_score),
                                    "penalty": BIAS_PENALTY
                                })

                                # Only apply one bias penalty per voter per question
                                break

    # Calculate total penalties for each member
    bias_penalties = {member: sum(bias_penalties_by_question[q][member] for q in range(1, 11)) for member in
                      group_members}
    absence_penalties = {member: sum(absence_penalties_by_question[q][member] for q in range(1, 11)) for member in
                         group_members}

    # Calculate final scores after penalties
    final_scores = {}
    for member in group_members:
        final_scores[member] = raw_scores[member] + bias_penalties[member] + absence_penalties[member]

    return (question_scores, raw_scores, final_scores,
            bias_penalties, absence_penalties,
            bias_penalties_by_question, absence_penalties_by_question,
            voting_record, bias_records,
            question_member_means, question_member_thresholds)


def generate_voting_data(group_members, include_bias=True, bias_percentage=20):
    """
    Generate simulated voting data for a group across 10 questions.

    Parameters:
        group_members (list): List of member identifiers
        include_bias (bool): Whether to include some intentional bias in the voting data
        bias_percentage (int): Percentage of votes that should contain bias

    Returns:
        dict: Simulated voting data
    """
    # Initialize empty voting data structure
    simulated_votes = {member: {} for member in group_members}

    # Determine max ranks based on group size
    num_members = len(group_members)
    if 6 <= num_members <= 11:
        max_ranks = 2
    elif 12 <= num_members <= 17:
        max_ranks = 3
    elif 18 <= num_members <= 23:
        max_ranks = 4
    elif 24 <= num_members <= 29:
        max_ranks = 5
    else:
        raise ValueError("Group size must be between 6 and 29 members")

    # Create some "consensus" preferences for more realistic data
    consensus_preferences = {}
    for question in range(1, 11):
        # For each question, create a different consensus ranking of members
        shuffled_members = group_members.copy()
        np.random.shuffle(shuffled_members)
        consensus_preferences[question] = shuffled_members

    # For each member and each question, generate votes
    for member in group_members:
        for question in range(1, 11):
            # Skip some votes randomly to simulate absence (10% chance)
            if np.random.random() > 0.1:  # 90% participation rate
                # Get list of members excluding self
                potential_recipients = [m for m in group_members if m != member]

                # Determine if this vote will be biased
                is_biased = include_bias and np.random.random() < (bias_percentage / 100)

                if is_biased:
                    # Create biased vote by promoting a low-ranked member
                    consensus_order = [m for m in consensus_preferences[question] if m != member]
                    lowest_ranked = consensus_order[-3:]  # Bottom 3 members
                    biased_choice = np.random.choice(lowest_ranked)

                    # Create votes with biased choice at rank 1
                    votes = {}
                    votes[1] = biased_choice

                    # Fill remaining allowed ranks
                    other_options = [m for m in potential_recipients if m != biased_choice]
                    for rank in range(2, max_ranks + 1):
                        if other_options:
                            recipient = np.random.choice(other_options)
                            votes[rank] = recipient
                            other_options.remove(recipient)
                else:
                    # Follow general consensus with small variations
                    top_members = [m for m in consensus_preferences[question] if m != member][:max_ranks + 2]

                    # Choose top members based on max_ranks
                    if len(top_members) >= max_ranks:
                        chosen_recipients = np.random.choice(top_members, max_ranks, replace=False)
                    else:
                        # Fallback if not enough options
                        chosen_recipients = np.random.choice(potential_recipients,
                                                             min(max_ranks, len(potential_recipients)), replace=False)

                    # Assign ranks to chosen recipients
                    votes = {i + 1: recipient for i, recipient in enumerate(chosen_recipients)}

                simulated_votes[member][question] = votes

    return simulated_votes


def generate_voting_report(group_size=10):
    """
    Generate a complete voting report with mean-based threshold detection.

    Parameters:
        group_size (int): Number of members to simulate

    Returns:
        dict: Summary of results
    """
    # Set random seed for reproducibility
    np.random.seed(42)

    # Define group members
    group_members = [f"A{i}" for i in range(1, group_size + 1)]

    # Generate voting data
    simulated_votes = generate_voting_data(group_members)

    # Run the simulation
    results = calculate_group_voting_with_mean_threshold(group_members, simulated_votes)

    # Unpack results
    (question_scores, raw_scores, final_scores,
     bias_penalties, absence_penalties,
     bias_penalties_by_question, absence_penalties_by_question,
     voting_record, bias_records,
     question_member_means, question_member_thresholds) = results

    # Print mean scores and thresholds for each question and member
    print("\n===== MEAN SCORES AND THRESHOLDS BY QUESTION =====")
    for question in range(1, 11):
        if question_member_means[question]:
            print(f"\nQuestion {question}:")
            for member, mean_score in sorted(question_member_means[question].items()):
                threshold = question_member_thresholds[question][member]
                min_acceptable = max(0, mean_score - threshold)
                max_acceptable = mean_score + threshold
                print(f"  {member}: Mean score = {mean_score:.2f}, Threshold = ±{threshold:.2f}")
                print(f"     Acceptable range: [{min_acceptable:.2f} to {max_acceptable:.2f}]")

    # Print basic results
    print("\n===== VOTING RESULTS SUMMARY =====")

    print("\n1. RAW SCORES:")
    for member, score in sorted(raw_scores.items(), key=lambda x: x[1], reverse=True):
        print(f"{member}: {score} marks")

    print("\n2. BIAS PENALTIES:")
    for member, penalty in sorted(bias_penalties.items(), key=lambda x: x[1]):
        print(f"{member}: {penalty}")

    print("\n3. ABSENCE PENALTIES:")
    for member, penalty in sorted(absence_penalties.items(), key=lambda x: x[1]):
        print(f"{member}: {penalty}")

    print("\n4. FINAL SCORES:")
    for member, score in sorted(final_scores.items(), key=lambda x: x[1], reverse=True):
        print(f"{member}: {score}")

    print("\n5. DETAILED BIAS INSTANCES:")
    total_bias_instances = 0
    for question in range(1, 11):
        bias_instances = [record for record in bias_records[question] if 'absence' not in record]
        total_bias_instances += len(bias_instances)
        if bias_instances:
            print(f"\nQuestion {question}:")
            for record in bias_instances:
                print(f"  {record['voter']} gave {record['recipient']} rank {record['given_rank']} "
                      f"(score: {record['given_score']}, mean score: {record['mean_score']:.2f}, "
                      f"acceptable range: [{record['mean_score'] - record['threshold']:.2f} to {record['mean_score'] + record['threshold']:.2f}], "
                      f"deviation: {record['deviation']:.2f}, penalty: {record['penalty']})")

    print(f"\nTotal number of bias instances detected: {total_bias_instances}")

    return {
        'raw_scores': raw_scores,
        'bias_penalties': bias_penalties,
        'absence_penalties': absence_penalties,
        'final_scores': final_scores,
        'question_member_means': question_member_means,
        'question_member_thresholds': question_member_thresholds,
        'bias_instances': total_bias_instances
    }


# If run as the main script, execute the voting report generation
if __name__ == "__main__":
    # For demonstration, run with different group sizes
    for size in [10, 15, 20]:
        print(f"\n\n=========== SIMULATION WITH {size} MEMBERS ===========")
        generate_voting_report(size)

