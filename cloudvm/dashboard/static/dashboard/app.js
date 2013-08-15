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

function IndexController($scope, $http) {
  function post(url) {
    $scope.busy = true;
    return $http.post(url).success(function(data) {
      $scope.busy = false;
    });
  }

	function store(data) {
    $scope.model = data;
		$scope.model.manifest.can_destroy = _.reduce($scope.model.manifest.groups, function(memo, group) { return memo && !group.any_running && group.any_created; }, true);
		$scope.model.manifest.can_kill = _.reduce($scope.model.manifest.groups, function(memo, group) { return memo || group.any_running; }, false);
	}

  $scope.busy = true;
  $http.get('/status').success(function(data) {
		store(data);
    $scope.busy = false;
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
}
