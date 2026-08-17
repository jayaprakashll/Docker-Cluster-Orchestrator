const API_BASE = (
  import.meta.env.VITE_MANAGER_URL || "http://localhost:8000"
).replace(/\/+$/, "");

class ManagerAPIError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.name = "ManagerAPIError";
    this.status = status;
  }
}

async function request(method, path, options = {}) {
  const {
    params,
    body,
    timeout = 15000,
  } = options;

  let url = `${API_BASE}${path}`;

  if (params) {
    const query = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        query.set(key, String(value));
      }
    });

    const queryString = query.toString();

    if (queryString) {
      url += `?${queryString}`;
    }
  }

  const controller = new AbortController();

  const timer = setTimeout(() => {
    controller.abort();
  }, timeout);

  try {
    const response = await fetch(url, {
      method,
      headers: body
        ? {
            "Content-Type": "application/json",
            Accept: "application/json",
          }
        : {
            Accept: "application/json",
          },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    clearTimeout(timer);

    let data = {};
    const text = await response.text();

    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = {
          raw: text,
        };
      }
    }

    if (!response.ok) {
      const detail =
        data?.detail ||
        data?.message ||
        data?.raw ||
        response.statusText ||
        "Unknown error";

      throw new ManagerAPIError(
        `${method} ${path} failed (${response.status}): ${detail}`,
        response.status
      );
    }

    return data;
  } catch (error) {
    clearTimeout(timer);

    if (error instanceof ManagerAPIError) {
      throw error;
    }

    if (error.name === "AbortError") {
      throw new ManagerAPIError(
        `Request timed out: ${method} ${path}`
      );
    }

    throw new ManagerAPIError(
      `Cannot connect to Manager at ${API_BASE}: ${error.message}`
    );
  }
}

function encoded(value) {
  return encodeURIComponent(String(value));
}

export const api = {
  health() {
    return request("GET", "/api/health");
  },

  getMachineHealth(activeOnly = false) {
    return request("GET", "/api/health/machines", {
      params: {
        active_only: activeOnly,
      },
    });
  },

  getMachines() {
    return request("GET", "/api/machines");
  },

  getStats() {
    return request("GET", "/api/stats");
  },

  getDatabaseInfo() {
    return request("GET", "/api/database");
  },

  getDeployments(activeOnly = false) {
    return request("GET", "/api/deployments", {
      params: {
        active_only: activeOnly,
      },
    });
  },

  pingMachine(machine) {
    return request(
      "POST",
      `/api/machines/${encoded(machine)}/ping`,
      {
        timeout: 10000,
      }
    );
  },

  getContainers(machine = null, allContainers = true) {
    return request("GET", "/api/containers", {
      params: {
        all: allContainers,
        ...(machine ? { machine } : {}),
      },
      timeout: 15000,
    });
  },

  getImages(machine = null) {
    return request("GET", "/api/images", {
      params: machine ? { machine } : {},
      timeout: 15000,
    });
  },

  runContainer(payload) {
    return request("POST", "/api/deployments", {
      body: payload,
      timeout: 60000,
    });
  },

  runContainerAuto(payload) {
    return request("POST", "/api/deployments/auto", {
      body: payload,
      timeout: 60000,
    });
  },

  getSchedulerScores() {
    return request("GET", "/api/scheduler/scores");
  },

  getSchedulerRecommendation() {
    return request("GET", "/api/scheduler/recommendation");
  },

  startContainer(container) {
    return request(
      "POST",
      `/api/containers/${encoded(container)}/start`,
      {
        timeout: 30000,
      }
    );
  },

  stopContainer(container) {
    return request(
      "POST",
      `/api/containers/${encoded(container)}/stop`,
      {
        timeout: 30000,
      }
    );
  },

  restartContainer(container) {
    return request(
      "POST",
      `/api/containers/${encoded(container)}/restart`,
      {
        timeout: 30000,
      }
    );
  },

  removeContainer(container, force = false) {
    return request(
      "DELETE",
      `/api/containers/${encoded(container)}`,
      {
        params: {
          force,
        },
        timeout: 30000,
      }
    );
  },

  inspectContainer(container) {
    return request(
      "GET",
      `/api/containers/${encoded(container)}/inspect`,
      {
        timeout: 15000,
      }
    );
  },

  getContainerLogs(container, tail = 200) {
    return request(
      "GET",
      `/api/containers/${encoded(container)}/logs`,
      {
        params: {
          tail,
        },
        timeout: 20000,
      }
    );
  },
};

export { ManagerAPIError };