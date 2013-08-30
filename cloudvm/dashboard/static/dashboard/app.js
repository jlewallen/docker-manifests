'use strict';


var app = angular.module("dashboard", [ 'ngRoute' ]).
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
}]);

app.config(function($httpProvider) {
  $httpProvider.interceptors.push(function($q) {
    return {
      'request': function(config) {
        return config;
      },
      'response': function(response) {
        return response;
      }
    }
  });
});

app.service("dockerService", function($http) {
  var self = this;
  self.model = null;

  this.refresh = function() {
    return $http.get('/status').success(function(data) {
      self.model = data;
    });
  };

  this.getInstance = function(name, callback) {
    self.refresh().success(function(data) {
      var instances = _.reduce(_.flatten(_.map(self.model.manifests, function(m) {
        return _.map(m.groups, function(g) {
          return g.instances;
        });
      })), function(memo, i) {
        memo[i.name] = i;
        return memo;
      },
      {});
      callback(instances[name]);
    });
  };

  this.getLogs = function(name) {
    return $http.get("/instances/" + name + "/logs");
  };
});

function LayoutCtrl($rootScope, $http) {
	$rootScope.busy = true; // Make a stack for concurrent busy, or even an angular http interceptor
}

function LogsController($scope, $routeParams, $rootScope, $http, dockerService) {
  $rootScope.busy = true;
  $scope.model = { };
	dockerService.getLogs($routeParams.name).success(function(data) {
    $scope.model.logs = data;
    $rootScope.busy = false;
  });
  dockerService.getInstance($routeParams.name, function(data) {
    $scope.model.instance = data;
    $rootScope.busy = false;
  });
}

function IndexController($scope, $rootScope, $http, dockerService) {
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
  dockerService.refresh().success(function(data) {
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

  $scope.recreate = function() {
    post($scope.model.kill_url).success(function(data) {
      store(data);
      post($scope.model.destroy_url).success(function(data) {
        store(data);
        post($scope.model.start_url).success(function(data) {
          store(data);
        });
      });
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
