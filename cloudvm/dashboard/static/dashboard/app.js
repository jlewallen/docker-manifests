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
  $httpProvider.interceptors.push(function($q, $rootScope) {
    return {
      'request': function(config) {
				$rootScope.outstandingXhr = $rootScope.outstandingXhr || [];
				$rootScope.outstandingXhr.push(true);
				$rootScope.busy = _.any($rootScope.outstandingXhr);
        return config;
      },
      'response': function(response) {
				$rootScope.outstandingXhr.pop();
				$rootScope.busy = _.any($rootScope.outstandingXhr);
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
    return self.refresh().success(function(data) {
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

function LayoutCtrl() {

}

function LogsController($scope, $routeParams, $http, dockerService) {
  $scope.model = { };
	dockerService.getLogs($routeParams.name).success(function(data) {
    $scope.model.logs = data;
  });
  dockerService.getInstance($routeParams.name, function(data) {
    $scope.model.instance = data;
  });
}

function IndexController($scope, $http, dockerService) {
  function post(url) {
    return $http.post(url).success(function(data) {
    });
  }

	function store(data) {
    $scope.model = data;
	}

  dockerService.refresh().success(function(data) {
		store(data);
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
