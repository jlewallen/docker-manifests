'use strict';

angular.module("dashboard", []).
  config(['$routeProvider', '$locationProvider', function($routeProvider, $locationProvider) {
    $routeProvider.when('/', {
      templateUrl: 'static/partials/landing.html',
      controller: IndexController
    }).
    otherwise({
      redirectTo: '/'
    });
    $locationProvider.html5Mode(true);
}]);

function IndexController($scope) {
  console.log("HI");
}
