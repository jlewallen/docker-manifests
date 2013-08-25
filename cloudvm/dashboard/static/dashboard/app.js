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

function LayoutCtrl($rootScope) {
	$rootScope.busy = true;
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
		$scope.model.manifest.can_destroy = _.reduce($scope.model.manifest.groups, function(memo, group) { return memo && !group.any_running && group.any_created; }, true);
		$scope.model.manifest.can_kill = _.reduce($scope.model.manifest.groups, function(memo, group) { return memo || group.any_running; }, false);
	}

  $rootScope.busy = true;
  $http.get('/status').success(function(data) {
		store(data);
    $rootScope.busy = false;
  });

  $scope.startManifest = function() {
    post($scope.model.manifest.start_url).success(function(data) {
			store(data);
    });
  }

  $scope.killManifest = function() {
    post($scope.model.manifest.kill_url).success(function(data) {
			store(data);
    });
  }

  $scope.destroyManifest = function() {
    post($scope.model.manifest.destroy_url).success(function(data) {
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
