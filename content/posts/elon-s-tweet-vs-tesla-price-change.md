---
title: "Elon’s tweet vs Tesla price change"
date: 2021-12-15
category: Work
cover: /images/9c6dde7f088b400fb7242a8d998bcbb4.png
legacy_url: https://aicpasean.wixsite.com/mysite/post/elon-s-tweet-vs-tesla-price-change
featured: true
views: 179
likes: 0
---

![](/images/9c6dde7f088b400fb7242a8d998bcbb4.png)![](/images/1c9457178d4b4f68af45dca96cb3518b.png)

**Conclusion**

We conducted simple linear regression and statistical analysis for the research question, 'How much does Elon Musk's number of tweets per day affect Tesla's stock price change?'. The R-squared in our model is 0.259, meaning that 25.9% of the variability in the response - stock price change is explained by the number of tweets through the linear regression model; in other words, the remaining 74.1% of the variability is due to characteristics that are not the number of tweets.

The predicted stock price change (%) equals 1.8928 plus 0.0704 times the number of tweets. If there is no tweeting, we would expect the stock price to have about 1.8928% change on average. For every one-unit increase in the number of tweets, we would predict that the stock price would change by 0.0704%. For example, if Elon tweets 20 times a day, it may trigger the stock price change about 1.8928 + 0.0704 x 20, or 3.30% on average in the 50-day moving average.

We also researched what a good R-squared value is. According to Investopedia, "What qualifies as a "good" R-Squared value will depend on the context. In some fields, such as the social sciences, even a relatively low R-Squared such as 0.5 could be considered relatively strong." Therefore, our R-squared analysis is worth considering because a person's tweeting trend is more closely related to the finance vs. social sciences than stock market indexes.

Source document: <https://github.com/cpasean/BusinessAnalytics/blob/main/Elon%E2%80%99s%20tweet%20vs%20Tesla%20price%20change.pdf>
