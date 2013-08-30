'use strict';


angular.module("dashboard", []).
  config(['$routeProvider', '$locationProvider', function($routeProvider, $locationProvider) {
    $routeProvider.when('/', {
      templateUrl: '/static/partials/landing.html',
      controller: IndexController
    });
    $routeProvider.when('/instances/:name/logs', {
      templateUrl: '/static/partials/logs.html',
      controller: LogsController
    });
    $routeProvider.otherwise({
      redirectTo: '/'
    });
    // $locationProvider.html5Mode(true);
}]);

function LayoutCtrl($rootScope) {
	$rootScope.busy = true;
}

function LogsController($scope, $routeParams, $rootScope, $http) {
	$http.get("/instances/" + $routeParams.name + "/logs").success(function(data) {
    $scope.model = { logs : data };
    $rootScope.busy = false;
  });
}

function IndexController($scope, $rootScope, $http) {
  function post(url) {
    $rootScope.busy = true;
    return $http.post(url).success(function(data) {
      $rootScope.busy = false;
    });
  }

	function store(data) {
    $scope.model = data;
	}

  $rootScope.busy = true;
  $http.get('/status').success(function(data) {
		store(data);
    $rootScope.busy = false;
  });

  $scope.start = function() {
    post($scope.model.start_url).success(function(data) {
			store(data);
    });
  }

  $scope.kill = function() {
    post($scope.model.kill_url).success(function(data) {
			store(data);
    });
  }

  $scope.destroy = function() {
    post($scope.model.destroy_url).success(function(data) {
			store(data);
    });
  }

  $scope.startGroup = function(group) {
    post(group.start_url).success(function(data) {
			store(data);
    });
  }

  $scope.killGroup = function(group) {
    post(group.kill_url).success(function(data) {
			store(data);
    });
  }

  $scope.destroyGroup = function(group) {
    post(group.destroy_url).success(function(data) {
			store(data);
    });
  }

  $scope.resizeGroup = function(group, size) {
    post(group.resize_url + "?size=" + size).success(function(data) {
			store(data);
    });
  }
}
