from collections import defaultdict
from math import isclose
from pickle import load
import random
from threading import Thread
import time

class TreePlanterGA:
    with open("./SmartAfforestation/data/tree_idx.dat", "rb") as __fh:
        tree_idx = load(__fh)

    with open("./SmartAfforestation/data/tree_info.dat", "rb") as __fh:
        tree_data = load(__fh)

    tree_types_count = len(tree_data)

    def __init__(self, AQI, area_limit, cost_limit, population, no_of_chromosomes=20):
        self.no_of_chromosomes = no_of_chromosomes
        self.area_limit = area_limit
        self.cost_limit = cost_limit
        self.population = population
        # assign zone and level
        self.Level, self.Zone = __class__.get_aqi_range(AQI)
        # initialize and get score, area & cost arrays
        self.score = [0] * __class__.tree_types_count
        self.area = [0] * __class__.tree_types_count
        self.cost = [0] * __class__.tree_types_count
        self.__get_score()
        # create sampling set
        self.sample_set = []
        self.__get_sampling_set()
        # initialize chromosomes
        self.__init_chromosomes()
        # best chromosome and its fitness encoutered so far
        self.best_fit = -float('inf')
        self.best_chromosome = None
        # some other parameters to keep track of fitness values during search
        self.total_fit = [-float('inf')]*no_of_chromosomes
        self.last_fit = -float('inf')
        self.rep_count = 0
        # searching on different threads
        self.threads = [None]*self.no_of_chromosomes

    @staticmethod
    def get_aqi_range(aqi):
        if aqi <= 50:
            return 'Good', 'Zone IV'
        elif 50 < aqi <= 100:
            return 'Moderate', 'Zone IV'
        elif 100 < aqi <= 150:
            return 'Unhealthy for sensitive groups', 'Zone III'
        elif 150 < aqi <= 200:
            return 'Unhealthy', 'Zone III'
        elif 200 < aqi <= 300:
            return 'Very Unhealthy', 'Zone II'
        else:
            return 'Hazardous', 'Zone I'

    def __get_score(self, w1=20, w2=5):
        tree_data = __class__.tree_data
        for i in range(__class__.tree_types_count):
            # f = w1*pi + w2*ui
            self.area[i] = tree_data[i]['Area']
            self.cost[i] = tree_data[i]['Cost']
            # pollution tolerance was per unit area, we covert them to per person per tree
            self.score[i] = (w1*tree_data[i][self.Zone] + w2*tree_data[i]['Utility'])*self.area[i]

    def __get_sampling_set(self):
        self.minc, self.maxc = float('inf'), -float('inf')
        for i in range(__class__.tree_types_count):
            count = min(self.cost_limit//self.cost[i], self.area_limit//self.area[i])
            self.minc = min(count, self.minc)
            self.maxc = max(count, self.maxc)
            self.sample_set.extend([i]*count)

    def __init_chromosomes(self):
        self.chromosomes = [[0]*len(self.sample_set) for i in range(self.no_of_chromosomes)]
        for c in self.chromosomes:
            choose = random.randint(self.minc, self.maxc)
            idx = random.sample(range(len(c)), choose)
            for i in idx:
                c[i] = 1

    def __crossover(self):
        M = len(self.sample_set)    # length of a chromosome
        X = self.no_of_chromosomes
        sorted_chrom = [i[0] for i in sorted(zip(self.chromosomes, self.total_fit),
                                             key=lambda i:i[1], reverse=True)][:X//2]
        for i in range(X//2):
            pivot = random.randint(1, M-2)
            # array modified in place
            self.chromosomes[i] = sorted_chrom[i][:pivot] + sorted_chrom[X//2-i-1][pivot:]
            self.chromosomes[X-i-1] = sorted_chrom[X//2-i-1][:pivot] + sorted_chrom[i][pivot:]
            self.chromosomes[X//2-i-1] = sorted_chrom[i]
            self.chromosomes[X//2+i] = sorted_chrom[X//2-i-1]

    @staticmethod
    def get_fitness(chromosome, score, sample_set, cost, area, cost_limit, area_limit, population):
        N = len(chromosome)
        total_cost = sum(cost[sample_set[i]] for i in range(N) if chromosome[i])
        total_area = sum(area[sample_set[i]] for i in range(N) if chromosome[i])
        if total_cost > cost_limit or total_area > area_limit:
            return -float('inf')
        # per capita
        total_score = sum(score[sample_set[i]] for i in range(N) if chromosome[i])/population
        fitness = 100*total_score
        return fitness

    def __assign_fitness(self, i):
        self.total_fit[i] = __class__.get_fitness(self.chromosomes[i], self.score, self.sample_set, self.cost,
                                                  self.area, self.cost_limit, self.area_limit, self.population)

    def run_search(self, runtime=5, max_rep=20, verbose=1):
        t_end = time.time() + runtime
        t = 0
        while time.time() <= t_end:
            for i in range(self.no_of_chromosomes):
                self.threads[i] = Thread(target=self.__assign_fitness, args=(i,))
                self.threads[i].start()
            for th in self.threads:
                th.join()

            curr_best_fit, curr_best_ch = min(zip(self.total_fit, self.chromosomes), key=lambda i:i[0])
            if curr_best_fit > self.best_fit:
                self.best_fit = curr_best_fit
                self.best_chromosome = curr_best_ch

            if t%100 == 0:
                if verbose == 2: print(*curr_best_ch, "\t", sep="", end="")
                if verbose >= 1: print(curr_best_fit)

            if isclose(curr_best_fit, self.last_fit, rel_tol=0.1):
                self.rep_count += 1
            self.last_fit = curr_best_fit
            t += 1
            if self.rep_count >= max_rep:
                self.rep_count = 0
                self.__init_chromosomes()
                continue
            self.__crossover()

    def get_results(self):
        trees = defaultdict(int)
        for i in range(len(self.sample_set)):
            if self.best_chromosome[i]:
                trees[__class__.tree_data[self.sample_set[i]]['Common name']] += 1

        total_score = sum(self.score[__class__.tree_idx[t]]*trees[t] for t in trees)/self.population
        used_area = sum(self.area[__class__.tree_idx[t]]*trees[t] for t in trees)
        used_cost = sum(self.cost[__class__.tree_idx[t]]*trees[t] for t in trees)
        return {'trees': dict(trees), 'score': total_score, 'area': used_area, 'cost': used_cost}
