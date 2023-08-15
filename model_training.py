import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import truncnorm

def understanding_noise():
    upper = 2
    lower = -2
    samples = truncnorm(lower, upper, loc=(upper + lower) / 2, scale=(upper - lower) / 6).rvs(1000000)
    plt.hist(samples, bins=50, density=True, alpha=0.6, color='b')
    x = np.linspace(-3, 3, 1000)
    pdf = truncnorm.pdf(x, lower, upper, loc=(upper + lower) / 2, scale=(upper - lower) / 6)
    plt.plot(x, pdf, 'r', linewidth=2)
    # Add labels and title
    plt.xlabel('Value')
    plt.ylabel('Probability Density')
    plt.title('Truncated Normal Distribution')
    # Saving the figure
    plt.savefig('./output/truncated_normal_distribution.png', dpi=300)

# because dataset is too small, too little information to do model training, thus generating new features
# chunks: how many data rows per simulation
def feature_engineering(data, chunks=500):
    newDF = pd.DataFrame()
    for rowID in range(0, len(data), 500):
        tmp = data[rowID:rowID+500]
        diffCol = [tmp['sensor'][rowID+i+1] - tmp['sensor'][rowID+i] for i in range(chunks-1)]
        # dropping the first row of each chunk to make use of the difference between i+1 row and i row
        tmp = tmp.tail(tmp.shape[0]-1)
        tmp = tmp.assign(difference=diffCol)
        newDF = pd.concat([newDF, tmp])
    newDF = newDF.reset_index()
    newDF.to_csv("./output/features.csv", index=False, header=['index', 'pump', 'valve', 'sensor', 'attack','difference'])

# dont have to clean the data because there is no null, empty or corrupted values
if __name__ == "__main__":
    all_data = pd.read_csv('./output/results.csv')

    # Understanding how the noise is distributed in the Probabilistic Distribution Function (PDF); sample image located in the repository (Function call is commented out)
    # understanding_noise()
    new_data = feature_engineering(all_data)