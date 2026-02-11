import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy


class PerformanceTracker:
    def __init__(self, data_returns, market_returns=None, annual_risk_free=0, alpha_var=0.05, period="d"):
        self.data_returns = data_returns
        self.market_returns = market_returns
        self.annual_risk_free = annual_risk_free
        self.alpha_var = alpha_var
        self.period = period
        if period not in ["d", "w"]:
            raise Exception("Period must be either daily or weekly.")

    def annualized_return(self, data_returns=False):
        if isinstance(data_returns, bool):
            data_returns = self.data_returns
        cumulative_return = (1 + data_returns).prod()
        if self.period == "d":
            years = len(data_returns) / 252
        elif self.period == "w":
            years = len(data_returns) / 52
        else:
            raise Exception("Period must be either daily or weekly.")
        annual_return = (cumulative_return ** (1 / years)) - 1
        return 100 * annual_return

    def annualized_std_return(self, data_returns=False):
        if isinstance(data_returns, bool):
            data_returns = self.data_returns
        std_dev = data_returns.std()
        if self.period == "d":
            annual_std_dev = std_dev * np.sqrt(252)
        elif self.period == "w":
            annual_std_dev = std_dev * np.sqrt(52)
        else:
            raise Exception("Period must be either daily or weekly.")
        return 100 * annual_std_dev

    def expected_return_capm(self):
        market_expected_returns = self.annualized_return(data_returns=self.market_returns)
        beta = self.portfolio_beta()
        camp_returns = self.annual_risk_free + beta * (market_expected_returns - self.annual_risk_free)
        return camp_returns

    def calculate_portfolio_alpha(self):
        return max(0, self.annualized_return() - self.expected_return_capm())

    def annualized_variance_return(self):
        std_dev = self.annualized_std_return()
        annual_var = std_dev ** 2
        return annual_var

    def sharpe_ratio(self):
        sharpe_ratio = (self.annualized_return() - self.annual_risk_free) / self.annualized_std_return()
        return sharpe_ratio

    def modigliani_ratio(self):
        stdev = self.annualized_std_return(data_returns=self.market_returns) / self.annualized_return()
        asset_pr = self.annualized_return() - self.annual_risk_free
        market_pr = self.annualized_return(data_returns=self.market_returns) - self.annual_risk_free
        modigliani_ratio = stdev * asset_pr - market_pr
        return modigliani_ratio

    def modified_sharpe_ratio(self):
        modified_sharpe_ratio = (self.annualized_return() - self.annual_risk_free) / self.annualized_variance_return()
        return modified_sharpe_ratio

    def treynor_ratio(self):
        treynor_ratio = (self.annualized_return() - self.annual_risk_free) / self.portfolio_beta()
        return treynor_ratio

    def max_drawdown(self):
        cumulative_return = np.cumprod(1 + self.data_returns)
        rolling_max = np.maximum.accumulate(cumulative_return)
        drawdown = (cumulative_return - rolling_max) / rolling_max
        max_drawdown = np.min(drawdown)
        return max_drawdown * 100

    def portfolio_beta(self):
        if isinstance(self.market_returns, pd.Series):
            covariance = np.cov(self.data_returns, self.market_returns, ddof=0)[0, 1]
            market_variance = np.var(self.market_returns, ddof=0)
            beta = covariance / market_variance
            return beta
        else:
            return None

    def portfolio_value_at_risk(self):
        return 100 * scipy.stats.norm.ppf(self.alpha_var, np.mean(self.data_returns), np.std(self.data_returns))

    def portfolio_media_perda_esperada(self):
        return 100 * self.data_returns[self.data_returns < self.portfolio_value_at_risk() / 100].mean()

    def plot_cumulative_returns(self):
        if isinstance(self.market_returns, pd.Series):
            portfolio_cum_returns = (1 + self.data_returns).cumprod()
            market_cum_returns = (1 + self.market_returns).cumprod()
            plt.plot(portfolio_cum_returns.index, portfolio_cum_returns, label='Portfolio')
            plt.plot(market_cum_returns.index, market_cum_returns, label='Market Index')
            plt.xlabel('Date')
            plt.ylabel('Cumulative Return')
            plt.title('Portfolio vs. Market Index Cumulative Returns')
            plt.legend()
            plt.show()

    def __call__(self, plot=False):
        result = {
            "sharpe": self.sharpe_ratio(),
            "modified_sharpe_ratio": self.modified_sharpe_ratio(),
            "treynor_ratio": self.treynor_ratio(),
            "modigliani_ratio": self.modigliani_ratio(),
            "max_drawdown": self.max_drawdown(),
            f"value_at_risk_{self.period}_{round(100 * (1 - self.alpha_var))}": self.portfolio_value_at_risk(),
            f"media_perda_esperada_{self.period}_{round(100 * (1 - self.alpha_var))}": self.portfolio_media_perda_esperada(),
            "beta": self.portfolio_beta(),
            "alpha": self.calculate_portfolio_alpha(),
            "annual_return": self.annualized_return(),
            "annual_std": self.annualized_std_return(),
            "capm_expected_return": self.expected_return_capm()
        }
        if plot:
            self.plot_cumulative_returns()
        return result