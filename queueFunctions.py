import random


class Fencer:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.fenced = []


class Pair:
    def __init__(self, one, two):
        self.one = one
        self.two = two


def check_pairs(first, second):
    return not (first.one in {second.one, second.two} or first.two in {second.one, second.two})


def reorder(pairs, fencers, max_unique_pairs):
    queue = []
    random.seed()
    queue.append(pairs[0])
    prev_pair = queue[0]
    prev2_pair = Pair(0, 0)

    cycle = 0
    refresh = 0
    added_to_reorder = 1

    while added_to_reorder < max_unique_pairs:
        if cycle > max_unique_pairs:
            queue.clear()
            queue.append(pairs[0])
            prev_pair = queue[0]
            added_to_reorder = 1
            cycle = 0
            refresh += 1

        rnd_pair_index = random.randint(0, max_unique_pairs - 1)
        chosen = prev_pair

        while chosen == prev_pair or chosen in queue:
            rnd_pair_index = random.randint(0, max_unique_pairs - 1)
            chosen = pairs[rnd_pair_index]

        check = True
        if added_to_reorder > 1:
            check = check_pairs(chosen, queue[added_to_reorder - 2])

        if check_pairs(chosen, queue[added_to_reorder - 1]) and check:
            queue.append(chosen)
            prev2_pair = prev_pair
            prev_pair = chosen
            added_to_reorder += 1
        else:
            cycle += 1

    print("refreshes:", refresh)
    return [(fencers[pair.one].name, fencers[pair.two].name) for pair in queue]


def main(names):
    num_fencers = len(names)
    fencers = [Fencer(name, i) for i, name in enumerate(names)]
    pairs = []

    max_unique_pairs = (num_fencers * (num_fencers - 1)) // 2
    added_pairs = 0

    while added_pairs < max_unique_pairs:
        one = random.randint(0, num_fencers - 1)
        two = random.randint(0, num_fencers - 1)

        while one == two:
            two = random.randint(0, num_fencers - 1)

        already_fenced = two in fencers[one].fenced

        if not already_fenced:
            new_pair = Pair(fencers[one].id, fencers[two].id)
            pairs.append(new_pair)
            fencers[one].fenced.append(fencers[two].id)
            fencers[two].fenced.append(fencers[one].id)
            added_pairs += 1

    ordered_pairs = reorder(pairs, fencers, max_unique_pairs)
    return ordered_pairs