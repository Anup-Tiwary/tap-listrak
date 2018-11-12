# Changelog

## 2.0.7
  * Update version of `requests` to `0.20.0` in response to CVE 2018-18074

## 2.0.6
  * Update `contacts` in schema to use `listId` and `emailAddress` [#9](https://github.com/singer-io/tap-listrak/pull/9/)

## 2.0.5
  * Fixes issue where tap would error if no messages returned [#8](https://github.com/singer-io/tap-listrak/pull/8)

## 2.0.4
  * Fixes issue introduced in 2.0.3 where `sendDate` can be null on messages [#7](https://github.com/singer-io/tap-listrak/pull/7)

## 2.0.3
  * Uses lookback window for syncing activity [#6](https://github.com/singer-io/tap-listrak/pull/6)
  * Fixes contacts state to use `str` for both storing and retrieving

## 2.0.2
  * Adds more logging to sync mode [#5](https://github.com/singer-io/tap-listrak/pull/5)

## 2.0.1
  * Upgrade to Listrak REST API [#4](https://github.com/singer-io/tap-listrak/pull/4)

## 1.0.5
  * Fixes an error with raising exceptions on a 404 [#3](https://github.com/singer-io/tap-listrak/pull/3)

## 1.0.4
  * Fixes indentation in http request function

## 1.0.3
  * Remove backoff code and skip errors when a 404 comes back [#2](https://github.com/singer-io/tap-listrak/pull/2)
